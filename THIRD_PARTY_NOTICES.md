# Third-party notices

## Local translation model

The optional bundled-resource definition for local translation references:

- Repository: `Prukario/opus-mt-es-en-ct2-int8`
- Immutable revision: `ad91ad1697ea1761111ff4c179400796d085b347`
- License declared by the model repository: CC-BY-4.0
- Base model: `Helsinki-NLP/opus-mt-es-en`
- Base model license: Apache-2.0
- Languages: Spanish (`es`) → English (`en`)
- Runtime: CTranslate2 + SentencePiece

The application does not include the model weights in the source repository or Python wheel. When the operator downloads the model, the application stores the declared repository, revision, license and verified file metadata in the managed model directory.

When distributing the converted model, retain the applicable attribution and license notices from the model repository and its base model.
