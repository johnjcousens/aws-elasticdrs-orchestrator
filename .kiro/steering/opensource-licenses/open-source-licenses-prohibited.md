---
inclusion: manual
---

# Prohibited Open Source Licenses

When using 3rd party libraries always check the license of the library.
If library license is in the below list - always warn user about it!

## Prohibited Open Source Licenses

1. Affero General Public License (AGPL) 1.0
2. Affero General Public License (GNU AGPL) 3.0
3. Apple Public Source License 2.0
4. Community Data License Agreement (CDLA) - Sharing 1.0
5. Common Public Attribution License Version (CPAL) 1.0
6. Enna License (MIT Variant)
7. European Union Public License (EUPL) 1.1, 1.2
8. GNU Lesser General Public License (GNU LGPL) 3.0
9. GNU General Public License (GNU GPL) 3.0
10. Honest Public License (HPL) 1.0
11. NASA Open Source Agreement 1.3
12. Open Data Commons Open Database License (ODbL)
13. Open Software License (OSL) 3.0
14. Parity License 7.0
15. RealNetworks Public Source License 1.0
16. Server Side Public License (SSPL) 1.0

## Other Prohibited Licenses

1. Business Source License 1.1 (BUSL-1.1)
2. Commons Clause
3. Community Research and Academic Programming License
4. Confluent Community License
5. Creative Commons Attribution-NonCommercial (CC-NC) 1.0, 2.0, 2.5, 3.0, 4.0
6. Elastic License
7. Hugging Face Optimized Inference License 1.0 (HFOILv1.0)
8. Prosperity License 3.0
9. Redis Source Available License Agreement
10. UC Berkeley's Standard Copyright and Disclaimer Notice
11. University of Wisconsin Web Cache Simulator License

## Why These Are Prohibited

- **Copyleft licenses (GPL, AGPL, LGPL 3.0)**: Require derivative works to be released under the same license
- **SSPL**: Requires releasing entire service stack as open source
- **Non-commercial licenses (CC-NC)**: Cannot be used in commercial products
- **Commons Clause**: Restricts commercial use

## What To Do If You Find a Prohibited License

1. **Do not use the library** in production code
2. **Look for alternatives** with approved licenses
3. **Consult legal** if no alternatives exist and the library is critical
4. **Document the decision** if an exception is granted
