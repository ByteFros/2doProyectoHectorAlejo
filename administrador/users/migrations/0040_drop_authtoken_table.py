from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0039_alter_passwordresettoken_expires_at'),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS authtoken_token;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
