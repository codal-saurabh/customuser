from django.contrib.auth.tokens import PasswordResetTokenGenerator


class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        print('called')
        return str(timestamp)


default_token_generator = CustomPasswordResetTokenGenerator()
