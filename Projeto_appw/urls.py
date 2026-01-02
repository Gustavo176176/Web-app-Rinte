from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from Gestao_Consumos import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_user, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('registar/', views.registar, name='registar'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('dispositivos/', views.lista_dispositivos, name='lista_dispositivos'),
    path('adicionar_dispositivo/', views.adicionar_dispositivo, name='adicionar_dispositivo'),
    path('dispositivos/editar-post/<int:id>/', views.editar_dispositivo_post, name='editar_dispositivo_post'),
    path('dispositivos/apagar/<int:id>/', views.apagar_dispositivo, name='apagar_dispositivo'),

    path('definicoes/', views.definicoes, name='definicoes'),
    path('registar-consumo/', views.registar_consumo, name='registar_consumo'),
    path('editar-consumo/<int:id>/', views.editar_consumo, name='editar_consumo'),
    path('apagar-consumo/<int:id>/', views.apagar_consumo, name='apagar_consumo'),

    path('relatorios/', views.relatorios, name='relatorios'),
    path('editar-meta/<int:id>/', views.editar_meta, name='editar_meta'),
    path('apagar-meta/<int:id>/', views.apagar_meta, name='apagar_meta'),
    path('relatorios/pdf/<str:tipo>/<int:ano>/<int:mes>/', views.gerar_pdf, name='gerar_pdf'),

    path('fornecedores/', views.lista_fornecedores, name='lista_fornecedores'),
    path('associar-fornecedor/', views.associar_fornecedor, name='associar_fornecedor'),

    path('admin-painel/utilizadores/', views.gerir_utilizadores, name='gerir_utilizadores'),
    path('admin-painel/alterar-estado/<int:id_residente>/', views.alterar_estado_residente, name='alterar_estado_residente'),
]