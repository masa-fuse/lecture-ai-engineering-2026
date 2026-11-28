# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：`glossary_search_glossary({'query': '3レベル'})`
- STEP 3 の [tool call]：`fetch_fetch({'url': 'https://modelcontextprotocol.io/'})`（このあと勝手に `glossary_search_glossary({'query': 'MCP'})` も呼んでいた）
- STEP 4 の [tool call]：`aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 バージョニング 概要'})` → 2回目は英語で `aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Using versioning in S3 buckets overview'})`
- 気づき・疑問：aws を足すとツールが一気に5個増えて、名前が `aws_aws___…` になった。サーバー側のツール名がもともと `aws___` で始まっているらしい。fetch のときは入力が 1 万トークンを超えていて、ページの中身がそのままモデルに入るのが分かった。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎
- やったこと：`app/mcp_server.py` の TODO の下に `server.tool()(tools.get_lecture_summary)` を1行足した。エージェント側（`mcp_servers.json`・`mcp_agent.py`）は触っていない。
- 結果：`--list-tools` に `glossary_get_lecture_summary`（引数 `lecture: integer`）が増えた。「第2回では何を学びますか？」で `glossary_get_lecture_summary({'lecture': 2})` が呼ばれ、モデル応答 2 回で第2回の要点を答えた。`uv run pytest -q` は 21 passed。
- 気づき・疑問：エージェントは起動のたびにツールの一覧をサーバーに聞くので、サーバーに1行足すだけで使えるようになった。今回は検索の `search_glossary` ではなく、ちゃんと要点のほうを選んでいた。docstring の「第3回では何を学ぶ？のように」という例がそのまま効いている気がする。
