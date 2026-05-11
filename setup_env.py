from django.core.management.utils import get_random_secret_key

secret_key = get_random_secret_key()
# senha_ponto = input('Digite a senha para bater o ponto: ')
ips_permitidos = input('Digite os IPs permitidos separados por vírgula (ex: XXX.X.X.X,XXX.X.X.X): ')

with open('.env', 'w') as f:
    f.write(f'DJANGO_SECRET_KEY={secret_key}\n')
    f.write('DJANGO_DEBUG=True\n')
    f.write(f'ALLOWED_IPS={ips_permitidos}\n')
    # f.write(f'SENHA_PONTO={senha_ponto}\n')

print('.env criado com sucesso!')