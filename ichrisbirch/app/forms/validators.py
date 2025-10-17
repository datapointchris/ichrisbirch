from wtforms.validators import DataRequired
from wtforms.validators import ValidationError


class RequiredIf(DataRequired):
    """Validator which makes a field required if another field is set and has a truthy value.

    Ex:
    ```python
    class TestForm(FlaskForm):
        name = StringField('Name')
        has_nickname = BooleanField('Nickname')
        username = StringField('Username', validators=[RequiredIf('has_nickname')])
        submit = SubmitField('Submit')
    ```
    """

    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super().__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise ValidationError(f'{self.other_field_name} does not exist')
        if bool(other_field.data):
            super().__call__(form, field)
