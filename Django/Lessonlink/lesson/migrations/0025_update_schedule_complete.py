from django.db import migrations, models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('lesson', '0024_emailtemplate_province_and_more'),
    ]

    operations = [
        # 1. FIRST: Remove the old unique constraint
        migrations.AlterUniqueTogether(
            name='schedule',
            unique_together=set(),
        ),
        
        # 2. Add all new fields
        migrations.AddField(
            model_name='schedule',
            name='color',
            field=models.CharField(default='#3b82f6', max_length=20),
        ),
        migrations.AddField(
            model_name='schedule',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='schedule',
            name='end_time',
            field=models.TimeField(default='09:00:00'),
        ),
        migrations.AddField(
            model_name='schedule',
            name='instructor',
            field=models.CharField(default='Teacher', max_length=200),
        ),
        migrations.AddField(
            model_name='schedule',
            name='start_time',
            field=models.TimeField(default='08:00:00'),
        ),
        migrations.AddField(
            model_name='schedule',
            name='title',
            field=models.CharField(default='Class', max_length=200),
        ),
        migrations.AddField(
            model_name='schedule',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # 3. Change the day field choices
        migrations.AlterField(
            model_name='schedule',
            name='day',
            field=models.CharField(choices=[
                ('monday', 'Monday'),
                ('tuesday', 'Tuesday'), 
                ('wednesday', 'Wednesday'),
                ('thursday', 'Thursday'),
                ('friday', 'Friday'),
                ('saturday', 'Saturday'),
                ('sunday', 'Sunday')
            ], max_length=20),
        ),
        
        # 4. Make description nullable
        migrations.AlterField(
            model_name='schedule',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        
        # 5. Change user field to have related_name
        migrations.AlterField(
            model_name='schedule',
            name='user',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name='schedules',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        
        # 6. Remove old fields (AFTER removing constraint)
        migrations.RemoveField(
            model_name='schedule',
            name='subject',
        ),
        migrations.RemoveField(
            model_name='schedule',
            name='time',
        ),
        
        # 7. Change ordering
        migrations.AlterModelOptions(
            name='schedule',
            options={'ordering': ['day', 'start_time']},
        ),
    ]