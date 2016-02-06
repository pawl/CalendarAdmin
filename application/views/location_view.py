import requests
import StringIO

from base64 import b64encode
from application.views.custom_model_view import CustomModelView
from application.models import Location, Calendar, User
from wtforms.validators import ValidationError, required
from flask.ext.admin.form.upload import ImageUploadField, ImageUploadInput
from flask import g
from application import app, db


# fixes '/static/' before thumbnail URL
class ModifiedImageUploadInput(ImageUploadInput):
    def get_url(self, field):
        if field.thumbnail_size:
            filename = field.thumbnail_fn(field.data)
        else:
            filename = field.data

        if field.url_relative_path:
            filename = filename

        return 'http://i.imgur.com/' + filename + 't.jpg'  # small thumbnail


# override ImageUploadField to upload images to imgur instead
# idea from quokka: https://github.com/pythonhub/quokka/blob/f89653bbe753319ca204d8e3aba482492f4858fe/quokka/core/admin/fields.py
class ImgurImageField(ImageUploadField):
    widget = ModifiedImageUploadInput()

    def _delete_file(self, filename):
        pass

    def _save_file(self, data, filename):
        headers = {"Authorization": "Client-ID " + app.config.get("IMGUR_ID")}
        url = "https://api.imgur.com/3/upload.json"

        output = StringIO.StringIO()
        # required this to get it working on ubuntu: http://askubuntu.com/a/272095
        self.image.save(output, self.image.format)
        contents = output.getvalue()
        output.close()

        request = requests.post(
            url,
            headers=headers,
            data={
                'image': b64encode(contents),
            }
        )
        return request.json()['data']['id']


class LocationView(CustomModelView):
    # Override displayed fields
    column_list = ('title', 'calendar')

    column_labels = {
        'title': 'Possible Event Location (free-form text)',
        'image_url': 'Image',
        'country': 'Country (2 Letter Code)',
        'state': 'State (Only US or CA, 2 Letters)'
    }

    # TODO: fix - if multiple calendars have a location, it will clear all but 1
    form_columns = (
        'title',
        'address',
        'city',
        'state',
        'country',
        'description',
        'image_url',
        'calendar'
    )
    form_overrides = dict(image_url=ImgurImageField)

    def states(form, field):
        states = [
            'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC',
            'SK', 'YT', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL',
            'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM',
            'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN',
            'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]
        if (form.country.data in ['US', 'CA']) and (form.state.data not in states):
            raise ValidationError('Not a valid US or Canada state code.')
    def country_code(form, field):
        countries = [
            'AF', 'AX', 'AL', 'DZ', 'AS', 'AD', 'AO', 'AI', 'AQ', 'AG', 'AR',
            'AM', 'AW', 'AU', 'AT', 'AZ', 'BS', 'BH', 'BD', 'BB', 'BY', 'BE',
            'BZ', 'BJ', 'BM', 'BT', 'BO', 'BQ', 'BA', 'BW', 'BV', 'BR', 'IO',
            'BN', 'BG', 'BF', 'BI', 'KH', 'CM', 'CA', 'CV', 'KY', 'CF', 'TD',
            'CL', 'CN', 'CX', 'CC', 'CO', 'KM', 'CG', 'CD', 'CK', 'CR', 'CI',
            'HR', 'CU', 'CW', 'CY', 'CZ', 'DK', 'DJ', 'DM', 'DO', 'EC', 'EG',
            'SV', 'GQ', 'ER', 'EE', 'ET', 'FK', 'FO', 'FJ', 'FI', 'FR', 'GF',
            'PF', 'TF', 'GA', 'GM', 'GE', 'DE', 'GH', 'GI', 'GR', 'GL', 'GD',
            'GP', 'GU', 'GT', 'GG', 'GN', 'GW', 'GY', 'HT', 'HM', 'VA', 'HN',
            'HK', 'HU', 'IS', 'IN', 'ID', 'IR', 'IQ', 'IE', 'IM', 'IL', 'IT',
            'JM', 'JP', 'JE', 'JO', 'KZ', 'KE', 'KI', 'KP', 'KR', 'KW', 'KG',
            'LA', 'LV', 'LB', 'LS', 'LR', 'LY', 'LI', 'LT', 'LU', 'MO', 'MK',
            'MG', 'MW', 'MY', 'MV', 'ML', 'MT', 'MH', 'MQ', 'MR', 'MU', 'YT',
            'MX', 'FM', 'MD', 'MC', 'MN', 'ME', 'MS', 'MA', 'MZ', 'MM', 'NA',
            'NR', 'NP', 'NL', 'NC', 'NZ', 'NI', 'NE', 'NG', 'NU', 'NF', 'MP',
            'NO', 'OM', 'PK', 'PW', 'PS', 'PA', 'PG', 'PY', 'PE', 'PH', 'PN',
            'PL', 'PT', 'PR', 'QA', 'RE', 'RO', 'RU', 'RW', 'BL', 'SH', 'KN',
            'LC', 'MF', 'PM', 'VC', 'WS', 'SM', 'ST', 'SA', 'SN', 'RS', 'SC',
            'SL', 'SG', 'SX', 'SK', 'SI', 'SB', 'SO', 'ZA', 'GS', 'SS', 'ES',
            'LK', 'SD', 'SR', 'SJ', 'SZ', 'SE', 'CH', 'SY', 'TW', 'TJ', 'TZ',
            'TH', 'TL', 'TG', 'TK', 'TO', 'TT', 'TN', 'TR', 'TM', 'TC', 'TV',
            'UG', 'UA', 'AE', 'GB', 'US', 'UM', 'UY', 'UZ', 'VU', 'VE', 'VN',
            'VG', 'VI', 'WF', 'EH', 'YE', 'ZM', 'ZW'
        ]
        if form.country.data not in countries:
            raise ValidationError('Must be a valid ISO-3166 country code.')

    form_args = dict(
        state=dict(validators=[states]),
        country=dict(validators=[country_code]),
        calendar=dict(validators=[required()]),
    )

    # This is required as long as the calendar is in the form.
    # override forms to prevent users from seeing eachother's data: https://gist.github.com/mrjoes/5521548
    # Hook form creation methods
    def create_form(self):
        return self._use_filtered_parent(super(LocationView, self).create_form())

    def edit_form(self, obj):
        return self._use_filtered_parent(super(LocationView, self).edit_form(obj))

    def _use_filtered_parent(self, form):
        form.calendar.query_factory = self._get_parent_list
        return form

    def _get_parent_list(self):
        return Calendar.query.filter(Calendar.users.any(User.id == g.user.id)).all()

    def get_query(self):
        return Location.query.join(Location.calendar).\
                              filter(Calendar.users.any(User.id == g.user.id))

    def get_count_query(self):
        return self.session.query(db.func.count('*')).\
                            select_from(self.model).\
                            join(Location.calendar).\
                            filter(Calendar.users.any(User.id == g.user.id))
