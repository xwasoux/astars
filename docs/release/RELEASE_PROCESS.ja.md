# Astars Release Process

ステータス: Manual Process

関連文書:

- [RELEASE_POLICY.ja.md](RELEASE_POLICY.ja.md)
- [NEXT_RELEASE.ja.md](NEXT_RELEASE.ja.md)
- [../../CHANGELOG.md](../../CHANGELOG.md)

## この文書について

この文書は、合意済みのrelease scopeを公開可能な状態まで準備・検証し、tagとPyPI / npm artifactとして公開する反復可能な手順を定義する。特定versionの機能scopeは記載しない。

自動化を導入した場合も、CI workflowがこの手順のどこを代行するかを本書で明示する。

## Preconditions

- `NEXT_RELEASE`のStatusが`Planned`または`In Progress`である
- release objectiveとscopeが承認されている
- publish権限とregistry credentialを利用できる
- working treeの意図しない変更がない

credentialそのものやsecret取得手順はrepositoryへ記載しない。

## 1. Freeze Scope

- `NEXT_RELEASE`のScope / Non-Goalsを最終確認する
- release準備中は新機能を追加しない
- public API changeとmigration noteを確定する
- required evidenceの項目と実行方法が確定していることを確認する

## 2. Align Versions

少なくとも次のversionをtarget versionへ揃える。

- `Cargo.toml`のworkspace package version
- `bindings/python/pyproject.toml`
- `bindings/node/package.json`
- lockfileやgenerated package metadataにversionが含まれる場合はそれら

version更新後、dependency resolutionに意図しない変更がないか差分を確認する。

## 3. Finalize Changelog

- `CHANGELOG.md`の`Unreleased`内容を対象versionへ移す
- changelogの日付としてtag dateを記録する
- Added / Changed / Fixed / Removed / Known Limitationsを必要に応じて記載する
- issue番号やcommit列挙ではなく、利用者が観測する変更を書く

## 4. Verify Workspace

clean checkout相当の環境で、少なくとも次を実行する。

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo build --workspace --release
```

repository固有のtestが追加された場合は、この節へ正規手順として追加する。

## 5. Verify Python Artifact

```bash
cd bindings/python
maturin build --release
```

- 生成wheelをclean virtual environmentへinstallする
- installed packageを使ってPython exampleを実行する
- source checkoutを偶然importしていないことを確認する
- 対応platform / Python versionのartifactが揃っているか確認する

## 6. Verify Node Artifact

```bash
cd bindings/node
npm ci
npm run build
npm pack
```

- packageへ含まれるfileを確認する
- pack後のartifactをclean projectへinstallする
- installed packageを使ってNode exampleを実行する
- native binaryの対象platformを確認する

## 7. Mark Ready and Prepare Release Commit

- required evidence、version metadata、changelog、Known Limitationsが揃ったことを確認する
- blockerが残っていないことを確認し、release gateを`Ready`として承認する
- version、changelog、generated metadataだけが意図した差分になっているか確認する
- release commitに含める`NEXT_RELEASE`のStatusを`Releasing`へ更新する
- release commitを`main`へmergeする
- merge後のcommitでworkspace verificationを再確認する

`Ready`はgate承認状態であり、別commitとして残す必要はない。tag対象となるrelease commitでは、公開作業中であることを示す`Releasing`を記録する。

## 8. Tag

`main`上のrelease commitへannotated tagを作成する。

```bash
git tag -a vX.Y.Z -m "Astars vX.Y.Z"
git push origin vX.Y.Z
```

tagをpushする前に、tag target、version metadata、changelogを再確認する。push後はtagを移動しない。

## 9. Publish

事前に検証したsource / artifactと同一であることを確認して公開する。

### Python / PyPI

```bash
maturin upload path/to/verified.whl
```

事前にinstall testしたwheelをuploadする。複数platformのwheelを公開する場合は、各artifactのverification結果と対応づける。

### Node / npm

```bash
npm publish ./astars-native-X.Y.Z.tgz --access public
```

事前に`npm pack`してclean install testしたtarballをpublishする。

publish順は自動的なtransactionにならない。最初のregistryへ公開した時点から、同一versionを変更できない前提で扱う。

## 10. Verify Published Artifacts

- PyPI / npmにtarget versionが表示される
- registryからclean environmentへinstallできる
- Python / Nodeのsmoke testが通る
- package versionとruntimeの報告値が一致する
- tagがremote repositoryに存在する

## 11. Close Release

- `NEXT_RELEASE`のStatusを`Released`にする
- tag dateと各registryへのpublish完了日を区別して、release結果と既知の問題を記録する
- 必要ならGitHub Releaseを作成する
- 次のrelease検討を始める際に`NEXT_RELEASE`を書き換える

## Failure Handling

### Publish前のfailure

修正後にverificationを最初からやり直す。release tagをまだ共有していなければ、誤ったtagを公開しない。

### 一部registryへのpublish後のfailure

- publish済みartifactやtagを書き換えない
- 同一artifactの再試行で解決できるか確認する
- code / artifact変更が必要ならpatch versionを新たに発行する
- partial releaseであることをrelease recordへ明記する

## Automation Boundary

自動化候補:

- version整合check
- fmt / clippy / test / build
- wheel / native package build
- clean install smoke test
- tagをtriggerとしたregistry publish
- artifact provenance / checksum生成

自動化しても、scope freeze、breaking change判断、release承認は人間のdecision gateとして残す。
