from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('dojo', '0036_system_settings_email_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='system_settings',
            name='enable_jira_web_hook',
            field=models.BooleanField(default=False, verbose_name='Enable JIRA web hook. Please note: It is strongly recommended to whitelist the Jira server using a proxy such as Nginx.'),
        ),
        migrations.CreateModel(
            name='DojoMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('value', models.CharField(max_length=300)),
            ],
        ),
        migrations.AddField(
            model_name='dojometa',
            name='endpoint',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='endpoint_meta', to='dojo.Endpoint'),
        ),
        migrations.AddField(
            model_name='dojometa',
            name='product',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_meta', to='dojo.Product'),
        ),
        migrations.AlterUniqueTogether(
            name='dojometa',
            unique_together=set([('product', 'name'), ('endpoint', 'name')]),
        ),
        migrations.AddField(
            model_name='Engagement',
            name='deduplication_on_engagement',
            field=models.BooleanField(default=False)
        ),
        migrations.AddField(
            model_name='Test',
            name='description',
            field=models.TextField(blank=True, null=True)
        )
    ]