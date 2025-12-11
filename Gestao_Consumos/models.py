from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


#Tabela de proprietários / residentes
class Residente(models.Model):
    id_residente = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=200)
    password = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telemovel = models.CharField(max_length=20, unique=True)
    morada = models.CharField(max_length=255, blank=True, null=True)
    codigo_postal = models.CharField(max_length=20, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    
    #Se for 0 está inativo, se for 1 está ativo no sistema (Histórico guardado)
    status = models.IntegerField(default=0)
    #Django Admin
    class Meta:
        verbose_name = "Residente"
        verbose_name_plural = "Residentes"

    def __str__(self):
        return self.nome



#Tabela de tipo de gastos mensais por residente
class Tipo(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    
    OPCOES = (
        ('Agua', 'Água'),
        ('Luz', 'Luz'),
        ('Gas', 'Gás'),
    )
    tipo = models.CharField(max_length=20, choices=OPCOES)
    #Django Admin
    class Meta:
        verbose_name = "Tipo"
        verbose_name_plural = "Tipos"

    def __str__(self):
        return self.tipo
    

class Categoria(models.Model):
    OPCOES = (
        ('Consumidor', 'Consumidor'),
        ('Gerador', 'Gerador'),
    )
    id_categoria = models.AutoField(primary_key=True)

    categoria = models.CharField(max_length=20, choices=OPCOES)
    #0 - Inativo, 1 - Ativo
    status = models.IntegerField(default=0)
    #Django Admin
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.categoria




# Tabela de Dispositivos de cada residente
class Dispositivo(models.Model):
    id_dispositivo_residente = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    tipo = models.ForeignKey(Tipo, on_delete=models.PROTECT)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    residente = models.ForeignKey(Residente, on_delete=models.PROTECT)


    OPCOES_UNIDADE = (
        ('m3', 'Metro Cúbico (m³)'),
        ('kWh', 'Kilowatt-hora (kWh)'),
    )
    unidade = models.CharField(max_length=20, choices=OPCOES_UNIDADE)

    timestamp = models.DateTimeField(default=timezone.now)
    status = models.IntegerField(default=1)

    # Django Admin
    class Meta:
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivos"
    def __str__(self):
        return self.nome
        
    def clean(self):
    
        if not self.tipo_id:
            return  #se o tipo não estiver definido, sai da validação

        if self.tipo.tipo in ['Agua', 'Gas'] and self.unidade != 'm3':
            raise ValidationError('Para Água ou Gás, a unidade tem de ser m³.')
        
        if self.tipo.tipo == 'Luz' and self.unidade != 'kWh':
            raise ValidationError('Para Eletricidade, a unidade tem de ser kWh.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)



# Tabela de Registo de Consumos
class RegistoConsumo(models.Model):
    id_registo_consumo = models.AutoField(primary_key=True)
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.PROTECT) 
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)

    #Django Admin
    class Meta:
        verbose_name = "Registo de Consumo"
        verbose_name_plural = "Registos de Consumo"
        ordering = ['-timestamp'] 

    def __str__(self):
        return f"{self.dispositivo.nome} - {self.valor} ({self.timestamp.strftime('%Y-%m-%d')})"


#Tabela de fornecedores
class Fornecedor(models.Model):
    id_fornecedor = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    nif = models.CharField(max_length=20)
    morada = models.CharField(max_length=255, blank=True, null=True)
    # Status: 0 = Inativo, 1 = Ativo
    status = models.IntegerField(default=1) 
    
    #Django Admin
    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return self.nome
    

class FornecedorTipo(models.Model):
    id_fornecedor_tipo = models.AutoField(primary_key=True)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT)
    tipo = models.ForeignKey(Tipo, on_delete=models.PROTECT)
    OPCOES_UNIDADE = (
        ('m3', 'Metro Cúbico (m³)'),
        ('kWh', 'Kilowatt-hora (kWh)'),
    )
    unidade = models.CharField(max_length=20, choices=OPCOES_UNIDADE)
    
    status = models.IntegerField(default=1)
    #Django Admin
    class Meta:
        verbose_name = "Serviço do Fornecedor"
        verbose_name_plural = "Serviços dos Fornecedores"

    def __str__(self):
        return f"{self.fornecedor.nome} - {self.tipo.tipo}"
    


#Tabela de preços por fornecedor e tipo
class FornecedorValor(models.Model):
    id_fornecedor_valor = models.AutoField(primary_key=True)
    fornecedor_tipo = models.ForeignKey(FornecedorTipo, on_delete=models.PROTECT)
    valor = models.DecimalField(max_digits=5, decimal_places=3)
    timestamp = models.DateTimeField(default=timezone.now)

    #Django Admin
    class Meta:
        verbose_name = "Tarifa / Preço"
        verbose_name_plural = "Histórico de Tarifas"
        ordering = ['-timestamp'] #Ordenar por data decrescente

    def __str__(self):
        return f"{self.fornecedor_tipo} - {self.valor}€"
    

#Tabela que liga um fornecedor a um residente
class FornecedorResidente(models.Model):
    id_fornecedor_residente_tipo = models.AutoField(primary_key=True)
    fornecedor_tipo = models.ForeignKey(FornecedorTipo, on_delete=models.PROTECT)
    residente = models.ForeignKey(Residente, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Status: 0 = Inativo, 1 = Ativo
    status = models.IntegerField(default=1)

    #Django Admin
    class Meta:
        verbose_name = "Contrato de Residente"
        verbose_name_plural = "Contratos de Residentes"

    def __str__(self):
        return f"{self.residente.nome} - {self.fornecedor_tipo}"
    
#Tabela de orçamentos / limites por residente e tipo
class Orcamento_limite(models.Model):
    id_orcamento = models.AutoField(primary_key=True)
    residente = models.ForeignKey(Residente, on_delete=models.PROTECT)
    tipo = models.ForeignKey(Tipo, on_delete=models.PROTECT)
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)

    #Django Admin
    class Meta:
        verbose_name = "Orçamento / Limite"
        verbose_name_plural = "Orçamentos e Limites"

        unique_together = ('residente', 'tipo', 'timestamp') 


    def __str__(self):
        return f"{self.residente.nome} - Limite {self.tipo.tipo}: {self.valor}€"