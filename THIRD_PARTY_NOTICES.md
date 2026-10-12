# Third-party data attribution

## IndicPHI

The MEDAI document-type LogisticRegression pipeline was trained using English report text from the [IndicPHI synthetic dataset](https://huggingface.co/datasets/Sidharth1743/indicphi). The dataset card lists the dataset under the MIT License. The training used only report `text` as features and the source-provided `doc_type_id` as the target; MEDAI does not include the raw dataset files in this repository.

The IndicPHI dataset card states that persona seeds come from [NVIDIA Nemotron-Personas-India](https://huggingface.co/datasets/nvidia/Nemotron-Personas-India), which is listed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). The fitted MEDAI pipeline is an ML artifact produced from the English text subset; this attribution is provided in connection with that use. NVIDIA and the IndicPHI authors do not endorse MEDAI.

The raw dataset, saved evaluation report, and alternative LinearSVC artifact remain local and are excluded from this repository. The included LogisticRegression pipeline contains text-derived vocabulary and may reflect synthetic phrases or identifier-like tokens. The source dataset describes its identifiers as synthetic; this artifact is not suitable for clinical use.
