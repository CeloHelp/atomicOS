## Why

O atomicOS precisa transformar anotacoes brutas em notas atomicas estruturadas sem depender de servicos externos de IA ou copiar manualmente conteudo para o Obsidian. Esta mudanca formaliza a criacao do aplicativo desktop local que conecta uma UI produtiva no Windows, inferencia Ollama em um servidor Pop!_OS na rede e arquivamento direto no Vault do usuario.

## What Changes

- Introduz uma aplicacao desktop Python/Flet com interface retro-futurista em dark mode para captura de texto, titulo, destino no Vault e logs operacionais.
- Adiciona um fluxo de sintese de nota atomica que envia prompts para o modelo remoto `qwen2.5:3b` via API Ollama com configuracao deterministica.
- Adiciona gerenciamento local do Obsidian Vault, incluindo descoberta de pastas, criacao de diretorios e criacao de notas por CLI.
- Adiciona orquestracao assincrona/threaded para manter a UI responsiva durante chamadas de rede e escrita em disco.
- Adiciona tratamento basico de validacao, estados de carregamento, limpeza de resposta Markdown e feedback de sucesso ou erro no painel de logs.

## Capabilities

### New Capabilities
- `desktop-note-workflow`: Covers the end-to-end desktop workflow for collecting raw input, validating state, synthesizing an atomic note, writing it to the Vault, and updating UI feedback.
- `remote-ollama-synthesis`: Covers prompt construction, HTTP communication with the LAN Ollama server, response validation, and Markdown cleanup.
- `obsidian-vault-integration`: Covers Vault folder discovery, directory creation, Obsidian CLI invocation, and persistence validation.
- `responsive-flet-interface`: Covers the split-screen Flet UI, visual state transitions, logging panel, and non-blocking execution behavior.

### Modified Capabilities

None.

## Impact

- Affected code: new Python application modules for UI, orchestration/use cases, Ollama client, Obsidian manager, configuration, and tests.
- APIs: outbound HTTP POST to Ollama `/api/generate` on the local network.
- Dependencies: Python, Flet, requests, Obsidian CLI, local filesystem access, configured Obsidian Vault path, and reachable Ollama host running `qwen2.5:3b`.
- Systems: Windows desktop runtime, Pop!_OS inference server on LAN, and the user's Obsidian Vault.
