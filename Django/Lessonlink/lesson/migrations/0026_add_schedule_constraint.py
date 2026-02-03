from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lesson', '0025_update_schedule_complete'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='schedule',
            unique_together={('user', 'day', 'start_time', 'end_time')},
        ),
    ]