from django.db import models

# Constants
ORDER_ITEMS = 'order_items'
UPLOAD_PATH_ITEM_IMAGES = 'item_images/'


class ItemDetails(models.Model):
    item_details_id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=100)
    item_description = models.TextField(max_length=1000)

    def __str__(self):
        return self.item_name


class ItemImage(models.Model):
    image_id = models.AutoField(primary_key=True)
    item_details = models.ForeignKey(ItemDetails, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to=UPLOAD_PATH_ITEM_IMAGES)

    def __str__(self):
        return f"Image for {self.item_details.item_name}"


class Item(models.Model):
    item_id = models.AutoField(primary_key=True)
    item_details = models.ForeignKey(ItemDetails, on_delete=models.DO_NOTHING)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.item_details.item_name} - ${self.item_price}"


class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    order_date = models.DateTimeField(auto_now_add=True)
    order_total = models.DecimalField(max_digits=10, decimal_places=2)
    order_active = models.BooleanField(default=True)
    items = models.ManyToManyField(Item, through="OrderItem")

    def __str__(self):
        return f"Order #{self.order_id} - Total: ${self.order_total}"


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
    cart_id = models.AutoField(primary_key=True)
    items = models.ManyToManyField(Item, through="CartItem", related_name="carts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        return sum(cart_item.item.item_price * cart_item.quantity for cart_item in self.cartitem_set.all())

    def __str__(self):
        return f"Shopping Cart #{self.cart_id}"


class CartItem(models.Model):
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.item.item_details.item_name} x {self.quantity}"
