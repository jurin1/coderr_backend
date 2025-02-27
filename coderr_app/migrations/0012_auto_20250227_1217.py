from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_dummy_users(apps, schema_editor):
    CustomUser = apps.get_model('coderr_app', 'CustomUser')
    Profile = apps.get_model('coderr_app', 'Profile')

    user1 = CustomUser.objects.create_user(
        username='andrey',
        email='andrey@example.com',
        password='asdasd', 
        type='customer'
    )
    Profile.objects.create(
        user=user1,
        first_name='Andrey',
        last_name='Customer',
        location='Musterstadt',
        description='Ein Testkunde'
    )

    user2 = CustomUser.objects.create_user(
        username='kevin',
        email='kevin@example.com',
        password='asdasd24', 
        type='business'
    )
    Profile.objects.create(
        user=user2,
        first_name='Kevin',
        last_name='Business',
        location='Musterstadt',
        description='Ein Test Business User',
        working_hours='Mo-Fr 9-17 Uhr'
    )


def delete_dummy_users(apps, schema_editor):
    CustomUser = apps.get_model('coderr_app', 'CustomUser')
    CustomUser.objects.filter(username='dummycustomer').delete()
    CustomUser.objects.filter(username='dummybusiness').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('coderr_app', '0011_review'),
    ]

    operations = [
        migrations.RunPython(create_dummy_users, delete_dummy_users),
    ]