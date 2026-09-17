# SQLite Local como Fonte Única da Verdade

O projeto foi desenhado para ser implantado em computadores de bibliotecas operados por equipes sem capacitação técnica em administração de banco de dados. Decidimos manter o SQLite como único mecanismo de persistência local, evitando PostgreSQL, MySQL ou serviços de banco gerenciados. O modelo de arquivo único simplifica drasticamente a instalação inicial (`setup.bat`), o backup manual e a recuperação em caso de falha de hardware, sem comprometer a integridade graças ao uso de transações atômicas com `select_for_update` nos pontos concorrentes.
