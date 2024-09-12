# Runtime Rollback Action

## Descrição

Este pipeline realiza um rollback self-hosted para uma tag previamente implantada.

## Inputs

Os seguintes inputs devem ser configurados no GitLab CI:

- `CLIENT_ID`: Account client id (obrigatório)
- `CLIENT_KEY`: Account client secret key (obrigatório)
- `CLIENT_REALM`: Account client realm (obrigatório)
- `WORKSPACE`: Workspace usado para deploy (obrigatório)
- `ENVIRONMENT`: Ambiente usado para deploy (obrigatório)
- `VERSION_TAG`: Tag da versão para rollback (obrigatório)
- `TF_STATE_BUCKET_NAME`: Bucket para salvar arquivos tfstate gerados (obrigatório)
- `TF_STATE_REGION`: Região de configuração para tfstate (obrigatório)
- `IAC_BUCKET_NAME`: Bucket para salvar arquivos iac gerados (obrigatório)
- `IAC_REGION`: Região de configuração para iac (obrigatório)
- `VERBOSE`: Configuração de verbose (opcional)
- `WORKDIR`: Caminho para o diretório onde o `.stk` está localizado (opcional, padrão: `./`)

## Como usar

1. Configure os inputs acima como variáveis de ambiente no GitLab CI.
2. Adicione o conteúdo do arquivo `.gitlab-ci.yml` ao seu repositório.
3. Execute o pipeline para realizar o rollback.

## Compatibilidade

A maioria dos comandos e ferramentas utilizados são compatíveis com o GitLab CI. No entanto, certifique-se de que o ambiente de execução possui as dependências necessárias instaladas, como `curl` e `python3`.