from django.contrib import admin
from .models import (
    Residente,
    Tipo,
    Categoria,
    Dispositivo,
    RegistoConsumo,
    Fornecedor,
    FornecedorTipo,
    FornecedorValor,
    FornecedorResidente,
    Orcamento_limite,
)

#Apenas o administrador consegue ver e gerir

@admin.register(Residente)
class ResidentesAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "telemovel", "status")
    search_fields = ("nome", "email", "telemovel")

@admin.register(Tipo)
class TipoAdmin(admin.ModelAdmin):
    list_display = ("id_tipo", "tipo")

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("id_categoria", "categoria", "status")

@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "categoria", "residente", "unidade", "status")
    list_filter = ("tipo", "categoria", "status")

@admin.register(RegistoConsumo)
class RegistoConsumoAdmin(admin.ModelAdmin):
    list_display = ("dispositivo", "valor", "timestamp")
    list_filter = ("dispositivo",)

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("nome", "nif", "status")

@admin.register(FornecedorTipo)
class FornecedorTipoAdmin(admin.ModelAdmin):
    list_display = ("fornecedor", "tipo", "unidade", "status")

@admin.register(FornecedorValor)
class FornecedorValorAdmin(admin.ModelAdmin):
    list_display = ("fornecedor_tipo", "valor", "timestamp")

@admin.register(FornecedorResidente)
class FornecedorResidenteAdmin(admin.ModelAdmin):
    list_display = ("residente", "fornecedor_tipo", "status", "timestamp")


@admin.register(Orcamento_limite)
class OrcamentoLimiteAdmin(admin.ModelAdmin):
    list_display = ("residente", "tipo", "valor", "timestamp")