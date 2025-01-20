import uuid
from operator import truediv
from ckeditor.fields import RichTextField
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, AbstractUser
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from utils.mail_service import send_registration_mail, send_group_invitation_mail

# Constants
UPLOAD_PATH_ITEM_IMAGES = 'item_images/'


class ModelDateMixin(models.Model):
    """
    Abstract model with created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ItemCategory(ModelDateMixin, models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=50)

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class ItemDetails(ModelDateMixin, models.Model):
    item_details_id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=100)
    categories = models.ManyToManyField(ItemCategory, related_name='items')
    item_description = RichTextField()

    def __str__(self):
        return self.item_name

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'


class ItemImage(models.Model):
    image_id = models.AutoField(primary_key=True)
    item_details = models.ForeignKey(ItemDetails, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to=UPLOAD_PATH_ITEM_IMAGES)

    def __str__(self):
        return f"Image for {self.item_details.item_name}"


class Item(ModelDateMixin, models.Model):
    item_id = models.AutoField(primary_key=True)
    item_details = models.ForeignKey(ItemDetails, on_delete=models.DO_NOTHING, related_name='items')
    item_price = models.DecimalField(max_digits=10, decimal_places=2)
    article_id = models.CharField(max_length=10, unique=True, default='')
    item_stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.item_details.item_name} - ${self.item_price}"


class OrderManager(models.Manager):
    def create_with_info_and_items(self, order_info_data, items_data, **kwargs):
        """
        Create an order with associated OrderInfo and OrderItems in a single transaction.
        Automatically calculates the order total.
        """
        with transaction.atomic():
            # Create the order
            order = self.create(**kwargs)

            # Create OrderInfo
            if order_info_data:
                OrderInfo.objects.create(order=order, **order_info_data)

            # Create OrderItems and calculate the total
            total = 0
            for item_data in items_data:
                item = item_data['item']
                quantity = item_data['quantity']

                # Validate item existence
                if not isinstance(item, Item):
                    raise ValueError(f"Invalid item: {item}")

                # Create the OrderItem
                OrderItem.objects.create(order=order, item=item, quantity=quantity)
                total += item.item_price * quantity

            # Update the order total
            order.order_total = total
            order.save(update_fields=['order_total'])

            return order


class OrderStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    SHIPPED = 'SHIPPED', _('Shipped')
    DELIVERED = 'DELIVERED', _('Delivered')
    CANCELLED = 'CANCELLED', _('Cancelled')
    RETURNED = 'RETURNED', _('Returned')


class Order(ModelDateMixin, models.Model):
    created_at = None
    order_id = models.AutoField(primary_key=True)
    order_date = models.DateTimeField(auto_now_add=True)
    order_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_active = models.BooleanField(default=True)
    order_status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    items = models.ManyToManyField(Item, through="OrderItem")
    user = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)

    objects = OrderManager()

    def __str__(self):
        return f"{self.order_id}"


class OrderInfo(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='order_info')
    buyer_name = models.CharField(max_length=100)
    buyer_email = models.EmailField()
    buyer_phone = models.CharField(max_length=15)
    buyer_address = models.TextField(max_length=300)

    def __str__(self):
        return f"Order {self.order.order_id} - {self.buyer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING)
    quantity = models.PositiveIntegerField(default=1)


class ShoppingCart(models.Model):
    """
    Model representing a shopping cart.
    """
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE)
    cart_id = models.AutoField(primary_key=True)
    items = models.ManyToManyField('Item', through="CartItem")
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        """
        Calculate the total price of all items in the shopping cart.
        """
        return sum(
            cart_item.item.item_price * cart_item.quantity
            for cart_item in self.cartitem_set.all()
        )

    def set_item(self, item, quantity=1):
        """
        Set the quantity of an item in the shopping cart.
        Removes the item if the quantity is less than 1.
        """
        if quantity < 1:
            self.cartitem_set.filter(item=item).delete()
        else:
            self.cartitem_set.update_or_create(item=item, defaults={'quantity': quantity})

    def clear(self):
        """
        Remove all items from the shopping cart.
        """
        self.cartitem_set.all().delete()

    def __str__(self):
        return f"Shopping Cart #{self.cart_id}"


class CartItem(models.Model):
    """
    Model representing an item in a shopping cart.
    """
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE)
    item = models.ForeignKey('Item', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.item.item_details.item_name} in Cart #{self.cart.cart_id}"


from django.db import models


class Address(models.Model):
    address_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='addresses')
    address = models.TextField(max_length=100)
    billing = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address}"

    class Meta:
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'billing'],
                condition=models.Q(billing=True),
                name='unique_billing_address_per_user'
            )
        ]

    def save(self, *args, **kwargs):
        if self.billing:
            # Ensure no other billing address is active for this user
            self.user.addresses.filter(billing=True).exclude(pk=self.pk).update(billing=False)
        # Save the instance
        super().save(*args, **kwargs)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The e-mail address must be provided"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_("Superuser muss is_staff=True haben."))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_("Superuser muss is_superuser=True haben."))

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser, PermissionsMixin):
    username = None
    email = models.EmailField(unique=True)
    company_identifier = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    verified = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

    @property
    def orders(self):
        return self.order_set.all()

    @property
    def shopping_cart(self):
        return self.shoppingcart

    @property
    def addresses(self):
        return self.addresses.all()

    @property
    def billing_address(self):
        return self.addresses.filter(billing=True).first()

    @property
    def full_name(self):
        return self.get_full_name() or self.email

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            ShoppingCart.objects.get_or_create(user=self)

        if not self.verified and not self.is_staff and self.first_name.strip() and self.last_name.strip():
            VerificationToken.objects.get_or_create(user=self)
            send_registration_mail(self)


    @transaction.atomic
    def set_inactive(self):
        self.is_active = False
        self.save(update_fields=['is_active'])
        self.shopping_cart.clear()
        self.save()

class VerificationToken(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='verification_token')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.user.email}"


User = get_user_model()

class CompanyGroup(models.Model):
    name = models.CharField(max_length=150, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_groups')
    members = models.ManyToManyField(User, related_name='member_groups',through='CompanyGroupMembership')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            CompanyGroupMembership.objects.get_or_create(user=self.owner, group=self, role=CompanyGroupRole.OWNER)

class CompanyGroupRole(models.TextChoices):
    OWNER = 'owner', _('Owner')
    MEMBER = 'member', _('Member')

class CompanyGroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(CompanyGroup, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(
        max_length=20,
        choices=CompanyGroupRole.choices,
        default=CompanyGroupRole.MEMBER
    )

    def __str__(self):
        return f"{self.user.email} in {self.group.name} as {self.get_role_display()}"


class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey('ShoppingList', on_delete=models.CASCADE, related_name='shopping_list_items')
    item = models.ForeignKey('Item', on_delete=models.CASCADE, related_name='shopping_list_items')
    quantity = models.PositiveIntegerField(default=1)  # Default Qty is 1

    def __str__(self):
        return f"{self.item} in {self.shopping_list}"


class ShoppingListStatus(models.TextChoices):
    DRAFT = 'draft', _('Draft')
    SUBMITTED = 'submitted', _('Submitted')
    APPROVED = 'approved', _('Approved')
    REJECTED = 'rejected', _('Rejected')

class ShoppingList(models.Model):
    title = models.CharField(max_length=150)
    group = models.ForeignKey(
        CompanyGroup,
        on_delete=models.CASCADE,
        related_name='shopping_lists',
        null=True,  # Optional für persönliche Listen
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(Item, through='ShoppingListItem', related_name='shopping_lists')
    status = models.CharField(
        max_length=20,
        choices=ShoppingListStatus.choices,
        default=ShoppingListStatus.DRAFT
    )
    is_personal = models.BooleanField(default=False)  # Neues Feld

    def __str__(self):
        return self.title

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(group__isnull=True, is_personal=True) | models.Q(group__isnull=False, is_personal=False),
                name="personal_or_group_list_constraint"
            )
        ]

class GroupInvitationStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    ACCEPTED = 'accepted', _('Accepted')
    DECLINED = 'declined', _('Declined')

class GroupInvitation(models.Model):
    email = models.EmailField()
    group = models.ForeignKey(CompanyGroup, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=GroupInvitationStatus.choices,
        default=GroupInvitationStatus.PENDING
    )
    group_invite_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation for {self.email} to {self.group.name}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.send_invitation_email()

    def send_invitation_email(self):
        send_group_invitation_mail(invitation=self)