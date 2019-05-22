from django.urls import path
from . import views

# Add a namespace to differentiate names of views between different apps
app_name = 'sys'

# These urls are all proceeded by '/system'
urlpatterns = [
    #path('', views.home, name='home'),
    path('', views.config_home, name='home'),   # Redirect the system home page to the config home page
    # Component views
    path('component/', views.comp_list, name='comp_list'),
    path('component/<component_id>/', views.comp_detail, name='comp_detail'),
    path('component/<component_id>/edit/', views.comp_edit, name='comp_edit'),
    path('component/<component_id>/form/', views.comp_form, name='comp_form'),
    path('component/<component_id>/add_par/', views.comp_add_par, name='comp_add_par'),
    path('component/<component_type>/create/', views.comp_create, name='comp_create'),
    path('component/<component_id>/delete/', views.comp_delete, name='comp_delete'),
    # Climate views
    path('climate/populate/', views.climate_populate, name='climate_populate'),
    # Project views
    path('project/', views.proj_list, name='proj_list'),
    path('project/create/', views.proj_create, name='proj_create'),
    path('project/<project_id>/delete/', views.proj_delete, name='proj_delete'),
    path('project/<project_id>/set_name/', views.proj_set_name, name='proj_set_name'),
    path('project/<project_id>/edit/', views.proj_edit, name='proj_edit'),
    path('project/<project_id>/form/', views.proj_form, name='proj_form'),
    # Configuration views
    path('configuration/', views.config_home, name='config_home'),
    path('configuration/<configuration_id>/set_name/', views.config_set_name, name='config_set_name'),
    path('configuration/<configuration_id>/set_climate/<climate_id>/', views.config_set_climate, name='config_set_climate'),
    path('configuration/<configuration_id>/set_project/<project_id>/', views.config_set_project, name='config_set_project'),
    path('configuration/<configuration_id>/add_component/<component_id>/', views.config_add_component, name='config_add_component'),
    path('configuration/<configuration_id>/remove_component/<component_id>/', views.config_remove_component, name='config_remove_component'),
    path('configuration/<configuration_type>/create/', views.config_create, name='config_create'),
    path('configuration/<configuration_id>/delete/', views.config_delete, name='config_delete'),
    path('configuration/<configuration_id>/invoke/', views.config_invoke, name='config_invoke'),
    # Visualization views
    path('visualization/list', views.vi_list, name='vi_list'),
    path('visualization/<configuration_id>/plot', views.vi_plot, name='vi_plot'),
]
