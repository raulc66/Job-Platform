import django_filters
from django.db.models import Q
from .models import Job


def _field_choices(model, field_name, fallback):
    try:
        field = model._meta.get_field(field_name)
        if getattr(field, "choices", None):
            return list(field.choices)
    except Exception:
        pass
    return fallback


EMPLOYMENT_CHOICES = _field_choices(
    Job,
    "employment_type",
    [
        ("full_time", "Full-time"),
        ("part_time", "Part-time"),
        ("contract", "Contract"),
        ("internship", "Internship"),
    ],
)

WORK_TYPE_CHOICES = _field_choices(
    Job,
    "work_type",
    [
        ("remote", "Remote"),
        ("hybrid", "Hybrid"),
        ("onsite", "La birou"),
    ],
)


class JobFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q", label="Cuvinte cheie")
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains", label="Locație")
    employment_type = django_filters.ChoiceFilter(method="filter_employment_type", choices=EMPLOYMENT_CHOICES, label="Tip angajare")
    work_type = django_filters.ChoiceFilter(method="filter_work_type", choices=WORK_TYPE_CHOICES, label="Mod lucru")
    has_salary = django_filters.BooleanFilter(method="filter_has_salary", label="Are salariu")

    class Meta:
        model = Job
        fields = ["location"]

    def filter_q(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(title__icontains=value)
            | Q(description__icontains=value)
            | Q(company__name__icontains=value)
        )

    def filter_employment_type(self, queryset, name, value):
        if not value:
            return queryset
        # Apply only if field exists
        field_names = {f.name for f in Job._meta.get_fields()}
        if "employment_type" in field_names:
            return queryset.filter(employment_type=value)
        return queryset

    def filter_work_type(self, queryset, name, value):
        if not value:
            return queryset
        field_names = {f.name for f in Job._meta.get_fields()}
        if "work_type" in field_names:
            return queryset.filter(work_type=value)
        return queryset

    def filter_has_salary(self, queryset, name, value: bool):
        if value is None:
            return queryset
        field_names = {f.name for f in Job._meta.get_fields()}
        has_min = "salary_min" in field_names
        has_max = "salary_max" in field_names
        if not (has_min or has_max):
            return queryset
        q = Q()
        if has_min:
            q |= Q(salary_min__isnull=False)
        if has_max:
            q |= Q(salary_max__isnull=False)
        return queryset.filter(q)