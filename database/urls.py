from django.urls import path, re_path

from . import api, views
urlpatterns = [
    path('', views.index, name='index'),
    #path('masters/', views.master_list, name='master_list'),
    path('drug_category/', views.drug_category, name='drug_category'),
    path('technique/', views.technique, name='technique'),
    path('cancer_type/', views.cancer_type, name='cancer_type'),
    path('immune_terms/', views.immune_terms, name='immune_terms'),
    path('browse_term/', views.browse_term, name='browse_term'),
    path('get_category_data/<str:category>/', views.get_category_data, name='get_category_data'),
    path('search/', views.search, name='search'),
    #path('drug_search/<str:pk>/', views.drug_search, name='drug_search'),
    path('get_data/<str:category>/<str:field>/<str:column>/', views.get_data, name='get_data'),
    path('get_columns/', views.get_columns, name='get_columns'),
    path('conditional_search/',views.conditional_search,name='conditional_search'),
    path('smiles_search/',views.smiles_search,name='smiles_search'),
    
    #*********************************************Tools ***********************************************************
    
    path('tanimoto_search/',views.tanimoto_search,name='tanimoto_search'),
    path('third_search/',views.third_search,name='third_search'),
    path('substructure_search/',views.substructure_search,name='substructure_search'),
    path('maccs_search/',views.maccs_search,name='maccs_search'),
    path('get_columns1/',views.get_columns1,name='get_columns1'),
    
    path('submit_data/',views.submit_data,name='submit_data'),

    #*********************************************API ***********************************************************

    path('api/v1/', api.index, name='api_index'),
    path('api/v1/status/', api.status, name='api_status'),
    path('api/v1/fields/', api.fields, name='api_fields'),
    path('api/v1/studies/<str:study_type>/', api.study_list, name='api_studies'),
    re_path(r'^api/v1/download/(?P<study>cell_line|animal_studies|patient_studies|all)\.(?P<fmt>csv|json)$', api.download, name='api_download'),
    path('api/v1/similarity/', api.similarity, name='api_similarity'),
]