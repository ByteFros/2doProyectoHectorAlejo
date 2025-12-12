"""
URLs del módulo de reportes y analytics
"""
from django.urls import path

from .views import (
    CompanyTripsSummaryView,
    EmployeeTripsSummaryView,
    ExemptDaysView,
    GeneralInfoView,
    MasterCompanyEmployeesView,
    TripsPerMonthView,
    TripsTypeView,
)

urlpatterns = [
    # Reportes de viajes
    path('report/viajes/', CompanyTripsSummaryView.as_view(), name='company-trips-summary'),
    path('report/trips-per-month/', TripsPerMonthView.as_view(), name='trips-per-month'),
    path('report/trips-type/', TripsTypeView.as_view(), name='trips-type'),
    path('report/exempt-days/', ExemptDaysView.as_view(), name='exempt-days'),
    path('report/general-info/', GeneralInfoView.as_view(), name='general-info'),

    # Reportes por empleado
    path('report/empleados/', EmployeeTripsSummaryView.as_view(), name='employee-trips-summary'),
    path('report/empresa/<int:empresa_id>/empleados/viajes/', MasterCompanyEmployeesView.as_view(),
         name='master-company-employees'),
]
