from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUser(AbstractUser):  
    TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('business', 'Business'),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='customer')

    def __str__(self):
        return self.username
    
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    file = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)  
    location = models.CharField(max_length=100, blank=True)
    tel = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    working_hours = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

class FileUpload(models.Model):
    file = models.FileField(upload_to='uploaded_files/')  
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.file)
    
class Offer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offers')
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='offer_images/', blank=True, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    @property
    def min_price(self):
        prices = [detail.price for detail in self.details.all() if detail.price is not None]
        return min(prices) if prices else None  

    @property
    def min_delivery_time(self):
        delivery_times = [detail.delivery_time_in_days for detail in self.details.all() if detail.delivery_time_in_days is not None]  # Corrected attribute name
        return min(delivery_times) if delivery_times else None

class OfferDetail(models.Model):
    OFFER_TYPE_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='details')
    title = models.CharField(max_length=255, blank=True, default="") 
    revisions = models.IntegerField(blank=True, null=True)  
    delivery_time_in_days = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    features = models.JSONField(default=list, blank=True)  
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPE_CHOICES, blank=True, default="") # Added offer_type

    def __str__(self):
        return f"Detail for {self.offer.title}"
    
class Order(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_orders')
    business_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='business_orders')
    offer_detail = models.ForeignKey(OfferDetail, on_delete=models.CASCADE, related_name="orders") 
    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField()
    offer_type = models.CharField(max_length=20) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.title}"
    
class Review(models.Model):
    business_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_received')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_given')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('business_user', 'reviewer')  
    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.business_user.username}"