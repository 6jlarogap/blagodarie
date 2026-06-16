import datetime, re

from django import forms
from django.conf import settings
from django.forms.widgets import SelectDateWidget, HiddenInput
from django.utils.dates import MONTHS
from django.utils.formats import get_format
from django.utils.safestring import mark_safe

from django.utils.translation import gettext as _

RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')

class UnclearSelectDateWidget(SelectDateWidget):
    month_unclear = False
    year_unclear = False

    def __init__(self, attrs=None, years=None, required=True):
        if not years:
            # С 20 декабря будет показан и следующий год
            years = list(range((datetime.date.today() + datetime.timedelta(days=12)).year, 1899, -1))
        return super(UnclearSelectDateWidget, self).__init__(attrs, years, required)

    def render(self, name, value, attrs=None, renderer=None):
        if isinstance(value, datetime.date):
            value = UnclearDate(value.year, value.month, value.day)

        try:
            year_val = value.year
            month_val = None if value.no_month else value.month
            day_val = None if value.no_day else value.day
        except AttributeError:
            year_val = month_val = day_val = None
            if isinstance(value, str):
                if settings.USE_L10N:
                    try:
                        input_format = get_format('DATE_INPUT_FORMATS')[0]
                        # Python 2.4 compatibility:
                        #     v = datetime.datetime.strptime(value, input_format)
                        # would be clearer, but datetime.strptime was added in
                        # Python 2.5
                        v = datetime.datetime.strptime(value, input_format)
                        year_val, month_val, day_val = v.year, v.month, v.day
                    except ValueError:
                        pass
                else:
                    match = RE_DATE.match(value)
                    if match:
                        year_val, month_val, day_val = [int(v) for v in match.groups()]

        # choices = [(i, i) for i in self.years]
        # year_html = self.create_select(name, self.year_field, value, year_val, choices, {'class': 'date-year'})
        year_html = self.create_year_input(name, self.year_field, year_val, {
                    'class': 'date-year',
                    'type': 'text',
                    'maxlength': '4',
        })
        # choices = zip(MONTHS.keys(), MONTHS.keys())
        choices = list(MONTHS.items())
        month_html = self.create_select(name, self.month_field, value, month_val, choices, {'class': 'date-month'})
        choices = [(i, i) for i in range(1, 32)]
        day_html = self.create_select(name, self.day_field, value, day_val,  choices, {'class': 'date-day'})

        output = []
        for field in SelectDateWidget._parse_date_fmt():
            if field == 'year':
                output.append(year_html)
            elif field == 'month':
                output.append(month_html)
            elif field == 'day':
                output.append(day_html)
        return mark_safe('\n'.join(output))

    def value_from_datadict(self, data, files, name):

        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        d = data.get(self.day_field % name)
        if not y and m == d == "0" or \
           not y and m == d == "":
            return None

        self.no_day = self.no_month = False

        if y:
            y = y.strip()
            if re.search(r'^0+$', y):
                y = "0"
        if (m or d) and not y:
            y = "0"
        if y:
            try:
                ud = UnclearDate(int(y), int(m), int(d))
            except ValueError:
                return '%s-%s-%s' % (y, m, d)
            else:
                return ud
        return data.get(name, None)

    def create_select(self, name, field, value, val, choices, attrs):
        from django.forms.widgets import Select
        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name
        choices.insert(0, self.none_value)
        local_attrs = self.build_attrs(attrs, extra_attrs={'id': field % id_})
        s = Select(choices=choices)
        select_html = s.render(field % name, val, local_attrs)
        return select_html

    def create_year_input(self, name, field, val, attrs):
        from django.forms.widgets import Input
        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name
        local_attrs = self.build_attrs(attrs, extra_attrs={'id': field % id_})
        s = Input(attrs=attrs)
        input_html = s.render(field % name, str(val).rjust(4, '0') if val else val, local_attrs)
        return input_html

class UnclearDateField(forms.DateField):
    widget = UnclearSelectDateWidget()
    empty_strings_allowed = True

    def __init__(self, *args, **kwargs):
        super(UnclearDateField, self).__init__(*args, **kwargs)
        self.widget.required = self.required

    def to_python(self, value):
        if not value:
            return None
        if isinstance(value, UnclearDate):
            return value
        return super(UnclearDateField, self).to_python(value)

    def prepare_value(self, value):
        if not value:
            return None
        if isinstance(value, str):
            re_m = re.search(r'^(\d{1,4})\-(\d{1,2})?-(\d{1,2})?$', value)
            if re_m:
                try:
                    y = int(re_m.group(1))
                    m = re_m.group(2)
                    m = int(m) if m else m
                    d = re_m.group(3)
                    d = int(d) if d else d
                    value = UnclearDate(y, m, d)
                except ValueError:
                    pass
        return value

    def clean(self, value):
        if not value and self.required:
            raise forms.ValidationError(self.error_messages['required'])
        if isinstance(value, str):
            value = self.prepare_value(value)
        if isinstance(value, str):
            if not re.search(r'^\d{1,4}\-\d{1,2}-\d{1,2}$', value):
                raise forms.ValidationError(
                    _('Была введена неверная дата (г-м-д): %s') % value
                )
            try:
                datetime.datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                y, m, d = value.split('-')
                raise forms.ValidationError(
                    _('Была введена неверная дата (дд-мм-гггг): %(day)s-%(month)s-%(year)s') % dict(
                    day=d.rjust(2,'0'), month=m.rjust(2,'0'), year=y.rjust(4,'0'),
                ))
        elif isinstance(value, UnclearDate) and not value.no_day and value.no_month:
            raise forms.ValidationError(_('Нет месяца в дате'))
        return value

