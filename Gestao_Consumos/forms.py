from django import forms
from .models import Residente, Dispositivo, RegistoConsumo, Orcamento_limite, Tipo, Categoria
from django.utils import timezone
import datetime

MESES_CHOICES = [(i, nome) for i, nome in enumerate(
    ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
     'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'], start=1)]
ANOS_CHOICES = [(i, i) for i in range(2025, 2031)]


# Formulário para registar um novo residente
class RegistoResidenteForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Residente
        fields = ['nome', 'email', 'telemovel', 'morada', 'codigo_postal', 'cidade', 'password']
        # Aplica classe Bootstrap 'form-control' a todos os campos de texto
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'}) for f in 
                   ['nome', 'telemovel', 'morada', 'codigo_postal', 'cidade']}
        widgets['email'] = forms.EmailInput(attrs={'class': 'form-control'})


# Formulário para adicionar/editar dispositivos (Luz, Água, Gás)
class DispositivoForm(forms.ModelForm):
    tipo = forms.ModelChoiceField(queryset=Tipo.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    # Campo categoria apenas com categorias ativas (status=1)
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(status=1), 
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Dispositivo
        fields = ['nome', 'categoria', 'tipo', 'unidade']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'unidade': forms.Select(attrs={'class': 'form-select'})
        }


# Formulário para editar o perfil do residente
class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = Residente
        fields = ['nome', 'email', 'telemovel', 'morada', 'codigo_postal', 'cidade']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'telemovel': forms.TextInput(attrs={'class': 'form-control'}),
            'morada': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
        }


# Formulário para registar consumo manual de um dispositivo
class ConsumoManualForm(forms.ModelForm):
    mes = forms.ChoiceField(choices=MESES_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    ano = forms.ChoiceField(choices=ANOS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = RegistoConsumo
        fields = ['dispositivo', 'valor']
        widgets = {
            'dispositivo': forms.Select(attrs={'class': 'form-select'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control'})
        }

    #pré-selecionar apenas dispositivos do residente atual
    def __init__(self, residente_obj, *args, **kwargs):
        self.residente_obj = residente_obj
        super().__init__(*args, **kwargs)
        if residente_obj:

            #Apenas residentes com status=1

            self.fields['dispositivo'].queryset = Dispositivo.objects.filter(residente=residente_obj, status=1)

    # Não permite registar mais de um consumo para o mesmo dispositivo no mesmo mês/ano
    def clean(self):
        cleaned_data = super().clean()
        dispositivo = cleaned_data.get('dispositivo')
        mes = int(cleaned_data.get('mes'))
        ano = int(cleaned_data.get('ano'))

        if dispositivo:
            qs = RegistoConsumo.objects.filter(dispositivo=dispositivo, timestamp__year=ano, timestamp__month=mes)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"Já existe um registo de consumo para {dispositivo.nome} em {mes}/{ano}."
                )
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.timestamp = timezone.make_aware(
            datetime.datetime(int(self.cleaned_data['ano']), int(self.cleaned_data['mes']), 1, 12, 0, 0)
        )
        if commit:
            instance.save()
        return instance



# Formulário para criar um novo limite orçamental mensal
class CriarMetaForm(forms.ModelForm):
    mes = forms.ChoiceField(choices=MESES_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    ano = forms.ChoiceField(choices=ANOS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    tipo = forms.ModelChoiceField(queryset=Tipo.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Orcamento_limite
        fields = ['valor', 'tipo']
        widgets = {'valor': forms.NumberInput(attrs={'class': 'form-control'})}

    def save(self, residente_obj, commit=True):
        instance = super().save(commit=False)
        instance.residente = residente_obj
        instance.timestamp = timezone.make_aware(
            datetime.datetime(int(self.cleaned_data['ano']), int(self.cleaned_data['mes']), 1, 12, 0, 0)
        )
        if commit:
            instance.save()
        return instance

# Formulário para editar um limite orçamental existente
class EditarMetaForm(forms.ModelForm):
    class Meta:
        model = Orcamento_limite
        fields = ['valor']
        widgets = {
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        }
