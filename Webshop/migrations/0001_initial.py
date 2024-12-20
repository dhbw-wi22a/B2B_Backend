# Generated by Django 5.1.4 on 2024-12-20 12:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('item_id', models.AutoField(primary_key=True, serialize=False)),
                ('item_price', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='ItemDetails',
            fields=[
                ('item_details_id', models.AutoField(primary_key=True, serialize=False)),
                ('item_name', models.CharField(max_length=100)),
                ('item_description', models.TextField(max_length=1000)),
            ],
            options={
                'verbose_name': 'Item',
                'verbose_name_plural': 'Items',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('order_id', models.AutoField(primary_key=True, serialize=False)),
                ('order_date', models.DateTimeField(auto_now_add=True)),
                ('order_total', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('order_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Webshop.item')),
            ],
        ),
        migrations.AddField(
            model_name='item',
            name='item_details',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='Webshop.itemdetails'),
        ),
        migrations.CreateModel(
            name='ItemImage',
            fields=[
                ('image_id', models.AutoField(primary_key=True, serialize=False)),
                ('image', models.ImageField(upload_to='item_images/')),
                ('item_details', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='Webshop.itemdetails')),
            ],
        ),
        migrations.CreateModel(
            name='OrderInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buyer_name', models.CharField(max_length=100)),
                ('buyer_email', models.EmailField(max_length=254)),
                ('buyer_phone', models.CharField(max_length=15)),
                ('buyer_address', models.TextField(max_length=300)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='order_info', to='Webshop.order')),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='Webshop.item')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Webshop.order')),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='items',
            field=models.ManyToManyField(through='Webshop.OrderItem', to='Webshop.item'),
        ),
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('cart_id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('items', models.ManyToManyField(related_name='carts', through='Webshop.CartItem', to='Webshop.item')),
            ],
        ),
        migrations.AddField(
            model_name='cartitem',
            name='cart',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Webshop.shoppingcart'),
        ),
    ]
