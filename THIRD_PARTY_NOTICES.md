# Third-party dependencies / 第三方依賴

The MIT license in `LICENSE` applies to this project's original skill instructions, scripts, and documentation. Dependencies remain subject to their own licenses. This source repository and its skill ZIP do not bundle PyMuPDF/MuPDF binaries or a Python virtual environment.

本專案 `LICENSE` 中的 MIT 授權適用於本專案原創的技能指令、程式與文件；依賴套件仍依各自授權使用。原始碼與技能 ZIP 不包含 PyMuPDF/MuPDF 執行檔或 Python 虛擬環境。

| Dependency / 依賴 | Version / 版本 | Upstream license / 上游授權 |
| --- | --- | --- |
| PyMuPDF, with its MuPDF engine | PyMuPDF 1.28.2 (see requirements.txt) | GNU Affero General Public License v3.0 (AGPL-3.0), or an Artifex commercial license |
| MCP Python SDK | 1.30.0, pinned to the maintained v1 API | MIT; see [upstream license](https://github.com/modelcontextprotocol/python-sdk/blob/v1.30.0/LICENSE) |

The MCP SDK installs additional transitive dependencies under their own licenses; installed package metadata and license files are authoritative. No third-party SDK source or binaries are vendored in this repository.

MCP SDK 的間接依賴另依各自授權；請以安裝套件的中繼資料與授權檔為準。本 Repo 未內嵌第三方 SDK 原始碼或二進位檔。

PyMuPDF's installed 1.28.2 package metadata identifies the dual licensing above. See [upstream licensing documentation](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright), the license files distributed with the installed package, and [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html).

PyMuPDF 1.28.2 的套件中繼資料標明上述雙重授權，請閱讀上游說明及安裝套件附帶的授權檔案。

Applying MIT to this project's original files does not relicense PyMuPDF or remove obligations associated with its use. Combined distribution or deployment may carry AGPL obligations; consult the upstream terms for the intended use, or obtain an appropriate commercial license from Artifex. Adding this notice alone does not establish compliance.

替本專案原創檔案採用 MIT，不會把 PyMuPDF 改成 MIT，也不會免除使用它時的授權義務。整合後的散布或部署可能涉及 AGPL 義務，應依實際用途查閱上游條款，或向 Artifex 取得適用的商業授權；僅加入此說明不代表已符合所有義務。
