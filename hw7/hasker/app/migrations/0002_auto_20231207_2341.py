from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', 'initial')
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='tags',
            field=models.ManyToManyField(blank=True, max_length=3,
                                         related_name='questions', to='app.Tag'),
        ),
        
        migrations.AlterField(
            model_name='tag',
            name='content',
            field=models.TextField(max_length=30, unique=True),
        )
    ]
