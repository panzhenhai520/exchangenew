# AMLO PDF Field Inventory

The tables below enumerate every interactive control in the three annotated AMLO templates (`1-01-fill.pdf`, `1-02-fill.pdf`, `1-03-fill.pdf`).

Columns:
- **PDF Field** ? the `/T` name embedded in the PDF.
- **Thai Label (raw)** ? literal text from the `/TU` alternate name (extracted without external translation; some glyphs may appear without tone marks because of the source encoding).
- **Romanized** ? automatic Thai romanisation via `pythainlp.transliterate.romanize` to help cross-check meaning.
- **Mapped Field** ? the corresponding `report_fields.field_name` once confirmed.
- **Notes** ? free-form observations (e.g. duplicates, shared areas).

> Tip: search within this document to locate repeated controls (e.g. multiple telephone boxes). Fill the **Mapped Field** column as you verify each binding so migrations/tests can be updated in the next step.
## AMLO-1-01 (CTR)

| PDF Field | Thai Label (raw) | Romanized | Mapped Field | Notes |
| --- | --- | --- | --- | --- |
| fill_3 | เพมเตม ครงท | phemtem khrongt |  | |
| fill_1 | ลงวนท | lo-ngwant |  | |
| fill_2 | รวมเอกสารจานวนทงสน | ruam-ekkasanchanuanthongson |  | |
| comb_1 | โปรดระบเลขทบตรประจาตวประชาชน | protraplektphatprachatataaprachachon | maker_id_number | |
| fill_4 | ๑.๑ ชอ-นามสกล | cocho cho namsakon |  | |
| fill_5 | ๑.๒ ทอย | cocho thoi |  | |
| undefined | undefined | yaithaitaaaaa |  | |
| fill_7 | โทรศพท | sorotphot | maker_phone | |
| fill_8 | โทรสาร | thorsan |  | |
| fill_9 | ๑.๓ อาชพ | cocho achop | maker_occupation_type | |
| fill_10 | สถานททางาน | sathantha-ngan | maker_occupation_employer | |
| fill_11 | โทรศพท | sorotphot |  | |
| fill_12 | ๑.๔ สถานทสะดวกในการตดตอ | cocho sathanthasaduaknaikattotto |  | |
| fill_13 | ๑.๕ หลกฐานทใชในการทาธรกรรม | cocho lokthanthachaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaich |  | |
| fill_57 | บตรประจาตวประชาชน | botprachataprachachon |  | |
| fill_56 | ขาราชการ | kharatchakan |  | |
| fill_55 | พนกงานรฐวสาหกจ | phanoknganonthawasahakot |  | |
| fill_14 | โทรศพท | sorotphot |  | |
| fill_15 | โทรสาร | thorsan |  | |
| fill_16 | เลขท | lekha |  | |
| fill_17 | ออกใหโดย | okhaidoi |  | |
| fill_18 | เมอ | moe |  | |
| fill_19 | หมดอาย | mot-ai |  | |
| fill_54 | สวนท ๒. ผรวมทาธรกรรม ผมอบหมาย หรอผมอบอานาจ | sawant chut phruamthatharakam phamopmai rophamop-anat |  | |
| comb_2 | ผรวมทาธรกรรม | phruamthatharakam |  | |
| fill_20 | ๒.๑ ชอ | cocho cho | joint_party_firstname | |
| fill_21 | สถานทตง | sathanthot | joint_party_address | |
| fill_22 | ๒.๒ ทอย | cocho thoi | joint_party_phone | |
| fill_23 | โทรศพท | sorotphot |  | |
| fill_24 | โทรสาร | thorsan |  | |
| fill_25 | ๒.๓ อาชพ | cocho achop |  | |
| fill_26 | สถานททางาน | sathantha-ngan |  | |
| fill_27 | โทรศพท | sorotphot |  | |
| fill_28 | ในกรณเปนนตบคคลใหระบประเภทการประกอบการ | naikronpennotkhonrairairairairairairairairairairairairairairairairairairairairairairairairairairaira |  | |
| fill_29 | ๒.๔ สถานทสะดวกในการตดตอ | cocho sathanthasaduaknaikattotto |  | |
| fill_30 | ๒.๕ หลกฐานทใชในการทาธรกรรม | cocho lokthanthachaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaich |  | |
| fill_60 | บตรประจาตวประชาชน | botprachataprachachon |  | |
| fill_59 | ขาราชการ | kharatchakan |  | |
| fill_58 | พนกงานรฐวสาหกจ | phanoknganonthawasahakot |  | |
| fill_31 | โทรศพท | sorotphot |  | |
| fill_32 | โทรสาร | thorsan |  | |
| fill_33 | เลขท | lekha |  | |
| fill_34 | ออกใหโดย | okhaidoi |  | |
| fill_35 | เมอ | moe |  | |
| fill_36 | หมดอาย | mot-ai |  | |
| fill_37 | วนททาธรกรรม | wonthatharakam | transaction_date_day | |
| fill_38 | เดอน | doen | transaction_date_month | |
| fill_39 | พ.ศ | phosa | transaction_date_year | |
| comb_3 | เขาบญชเลขท | khaobonchalekhot |  | |
| comb_5 | บญชทเกยวของ | bonchokhayakkoeokhong |  | |
| fill_48 | จานวน (บาท)_ฝาก งน  ซอตราสารการเงน  เชค  ดราฟต  อนๆ  ซอเงนตราตางประเทศ (โปรดระบสกลเงน)  อนๆ(ระบ) เขาบญชเลขท บญชทเกยวของ (หากม) | chanuan phabat afak ngon a sottrasankanngon a chek a drafot a ano a so-ngentratangprathet phaprotrapsakonngn a anophrabo khaobonchalekhot bonchokhayakkoeokhong phahakmo |  | |
| comb_4 | จากบญชเลขท | chakbonchalekhot |  | |
| comb_6 | บญชทเกยวของ | bonchokhayakkoeokhong |  | |
| fill_40 | อนๆ | ano |  | |
| fill_41 | อนๆ | ano |  | |
| fill_42 | อนๆ(ระบ | anophrap |  | |
| fill_43 | อนๆ(ระบ | anophrap |  | |
| undefined_2 | undefined | yaithaitaaaaa |  | |
| fill_49 | จานวน (บาท)_Row_1 | chanuan phabat tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha t |  | |
| fill_45 | รวมเงน | ruamngen | total_amount | |
| fill_50 | จานวน (บาท)_ | chanuan phabatha a |  | |
| fill_51 | จานวน (บาท)_Row_2 | chanuan phabat tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha tha t |  | |
| fill_46 | ๓.๒ ชอผรบประโยชนในการทาธรกรรม (ถาม | cocho chophropprayotchannaiathaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa phatham |  | |
| fill_47 | ๓.๓ วตถประสงคในการทาธรกรรม | cocho wottpharasongkhanaikanthathaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | transaction_purpose | |
| fill_1_2 | การรายงานทงหมดในชอง  “รวมเอกสารจานวนทงสน | kanrai-nganthongmotnaichong a ruam-ekkasanchanuanthongson |  | |
| fill_52 | แบบรายงานการทาธรกรรมทใชเงนสด | baeprai-ngankanthatthatthatthatthatthatthatthatthatthatthatthatthatthatthatthatthatthatthatthatthatt | report_number | |
| Check Box2 |  |  |  | |
| Check Box3 |  |  |  | |
| Check Box4 |  |  |  | |
| Check Box5 |  |  |  | |
| Check Box6 |  |  |  | |
| Check Box7 |  |  |  | |
| Check Box8 |  |  |  | |
| Check Box9 |  |  |  | |
| Check Box10 |  |  |  | |
| Check Box11 |  |  |  | |
| Check Box12 |  |  |  | |
| Check Box13 |  |  |  | |
| Check Box14 |  |  |  | |
| Check Box15 |  |  |  | |
| Check Box16 |  |  |  | |
| Check Box17 |  |  |  | |
| Check Box18 |  |  |  | |
| Check Box19 |  |  |  | |
| Check Box20 |  |  |  | |
| Check Box21 |  |  |  | |
| Check Box22 |  |  |  | |
| Check Box23 |  |  |  | |
| Check Box24 |  |  |  | |
| Check Box25 |  |  |  | |
| Check Box26 |  |  |  | |
| Check Box27 |  |  |  | |
| Check Box28 |  |  |  | |
| Check Box29 |  |  |  | |
| Check Box30 |  |  |  | |
| Check Box31 |  |  |  | |
| Check Box32 |  |  |  | |
| Check Box33 |  |  |  | |

## AMLO-1-02 (ATR)

| PDF Field | Thai Label (raw) | Romanized | Mapped Field | Notes |
| --- | --- | --- | --- | --- |
| fill_1 | เพมเตม ครงท | phemtem khrongt |  | |
| fill_2 | ลงวนท | lo-ngwant |  | |
| fill_3 | ๑.๑ ชอ-นามสกล | cocho cho namsakon |  | |
| fill_5 | ๑.๓ อาชพ | cocho achop |  | |
| fill_6 | โทรศพท | sorotphot |  | |
| fill_7 | โทรสาร | thorsan |  | |
| fill_8 | สถานททางาน | sathantha-ngan |  | |
| fill_9 | โทรศพท | sorotphot |  | |
| fill_10 | ๑.๔ สถานทสะดวกในการตดตอ [1] | cocho sathanthasaduaknaikattotto aa b |  | |
| fill_11 | ๑.๔ สถานทสะดวกในการตดตอ [2] | cocho sathanthasaduaknaikattotto rako |  | |
| fill_68 | ๑.๔ สถานทสะดวกในการตดตอ [3] | cocho sathanthasaduaknaikattotto aaho |  | |
| fill_67 | ๑.๔ สถานทสะดวกในการตดตอ [4] | cocho sathanthasaduaknaikattotto aipa |  | |
| fill_12 | โทรศพท | sorotphot |  | |
| fill_13 | โทรสาร | thorsan |  | |
| fill_14 | เลขท | lekha |  | |
| fill_15 | ออกใหโดย | okhaidoi |  | |
| fill_16 | เมอ | moe |  | |
| fill_17 | หมดอาย | mot-ai |  | |
| fill_18 | ๒.๑ ชอ | cocho cho |  | |
| fill_19 | สถานทตง | sathanthot |  | |
| fill_20 | ๒.๒ ทอย | cocho thoi |  | |
| fill_21 | โทรศพท | sorotphot |  | |
| fill_22 | โทรสาร | thorsan |  | |
| fill_23 | ๒.๓ อาชพ | cocho achop |  | |
| fill_24 | สถานททางาน | sathantha-ngan |  | |
| fill_25 | โทรศพท | sorotphot |  | |
| fill_26 | ในกรณทเปนนตบคคล ใหระบประเภทการประกอบการ [1] | naikranthapenentopkkhon rairappraphetkanprakopkan aa b |  | |
| fill_28 | ในกรณทเปนนตบคคล ใหระบประเภทการประกอบการ [2] | naikranthapenentopkkhon rairappraphetkanprakopkan rako |  | |
| fill_71 | ในกรณทเปนนตบคคล ใหระบประเภทการประกอบการ [3] | naikranthapenentopkkhon rairappraphetkanprakopkan aaho |  | |
| fill_70 | ในกรณทเปนนตบคคล ใหระบประเภทการประกอบการ [4] | naikranthapenentopkkhon rairappraphetkanprakopkan aipa |  | |
| fill_69 | ในกรณทเปนนตบคคล ใหระบประเภทการประกอบการ [5] | naikranthapenentopkkhon rairappraphetkanprakopkan ray |  | |
| fill_27 | ๒.๔ สถานทสะดวกในการตดตอ | cocho sathanthasaduaknaikattotto |  | |
| fill_29 | โทรศพท | sorotphot |  | |
| fill_30 | โทรสาร | thorsan |  | |
| fill_31 | เลขท | lekha |  | |
| fill_32 | ออกใหโดย | okhaidoi |  | |
| fill_33 | เมอ | moe |  | |
| fill_34 | หมดอาย | mot-ai |  | |
| fill_35 | วนททาธรกรรม | wonthatharakam |  | |
| fill_36 | เดอน | doen |  | |
| fill_37 | พ.ศ | phosa |  | |
| fill_38 | โปรดระบรายละเอยดของทรพยสน | protrabraila-aetkhongsongsongsongsongsongsongsongsongsongsongsongsongsongsongsongsongsongsongsongson |  | |
| fill_41 | ๓.๓ มลคาทรพยสนททาธรกรรมรวมทงสน | cocho monkhathonphaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa |  | |
| fill_42 | หากมลคาทรพยสนเปนเงนตราตางประเทศ โปรดระบจานวนและสกลเงน | hakamonkhathonphaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa protrapchanuanlaesakonnngngn |  | |
| fill_66 | (จานวนเงนทเปนตวอกษร) | phachanuanngentpentawekson |  | |
| fill_43 | ชอเจาของบญช | chochaokhongboncha |  | |
| fill_45 | ชอเจาของบญช | chochaokhongboncha |  | |
| fill_44 | ชอบญช | chopncha |  | |
| fill_46 | เกยวของโดย | koeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeo |  | |
| fill_47 | ๓.๖ ชอผรบประโยชนในการทาธรกรรม (ถาม | cocho chophropprayotchannaiathaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa phatham |  | |
| fill_48 | ๓.๗ วตถประสงคในการทาธรกรรม | cocho wottpharasongkhanaikanthathaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa |  | |
| fill_1_2 | การรายงานทงหมดในชอง “รวมเอกสารจานวนทงสน | kanrai-nganthongmotnaichong ruam-ekkasanchanuanthongson |  | |
| fill_52 | รายงานฉบบหลก | rai-nganchaboplok | report_number | |
| Check Box34 |  |  |  | |
| Check Box35 |  |  |  | |
| Check Box36 |  |  |  | |
| Check Box37 |  |  |  | |
| Check Box38 |  |  |  | |
| Check Box39 |  |  |  | |
| Check Box40 |  |  |  | |
| Check Box41 |  |  |  | |
| Check Box42 |  |  |  | |
| Check Box43 |  |  |  | |
| Check Box44 |  |  |  | |
| Check Box45 |  |  |  | |
| Check Box46 |  |  |  | |
| Check Box47 |  |  |  | |
| Check Box48 |  |  |  | |
| Check Box49 |  |  |  | |
| Check Box50 |  |  |  | |
| Check Box51 |  |  |  | |
| Check Box52 |  |  |  | |
| Check Box53 |  |  |  | |
| Check Box54 |  |  |  | |
| Check Box55 |  |  |  | |
| Check Box56 |  |  |  | |
| Check Box57 |  |  |  | |
| Check Box58 |  |  |  | |
| Check Box59 |  |  |  | |
| comb_1 | ๓.๔ เลขทบญชททาธรกรรม | cocho lekthabanchabanchabanchabanchabanchabanchabanchabanchabanchabanchabanchabanchabanchabanchabanchabanc |  | |
| comb_2 | ๓.๕ บญชทเกยวของ (หากม | cocho bonchokhayakkoeokhong phahakom |  | |
| t1 | [1] | aa b |  | |
| t2 | [2] | rako |  | |

## AMLO-1-03 (STR)

| PDF Field | Thai Label (raw) | Romanized | Mapped Field | Notes |
| --- | --- | --- | --- | --- |
| fill_51 | รายงานฉบบหลก | rai-nganchaboplok |  | |
| fill_1 | รวมเอกสารจานวนทงสน | ruam-ekkasanchanuanthongson |  | |
| comb_1 | โปรดระบเลขที่บตรประจาตวประชาชน | protraplekthibotprachatatatrachachon |  | |
| fill_2 | ๑.๑ ชื่อ-นามสกล | cocho chue namsakon |  | |
| fill_3 | ู่ | <PAD> |  | |
| fill_4 | ๑.๒ ทอย | cocho thoi |  | |
| fill_5 | โทรศพท | sorotphot |  | |
| fill_6 | โทรสาร | thorsan |  | |
| fill_7 | ๑.๓ อาชีพ | cocho achip |  | |
| fill_8 | สถานททางาน | sathantha-ngan |  | |
| fill_9 | โทรศพท | sorotphot |  | |
| fill_10 | ๑.๔ สถานทสะดวกในการตดต่อ | cocho sathanthasaduaknaikattotto |  | |
| fill_11 | ๑.๕ หลกฐานทใชในการทาธรกรรม | cocho lokthanthachaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaichaich |  | |
| fill_56 | บตรประจาตวประชาชน | botprachataprachachon |  | |
| fill_55 | ขาราชการ | kharatchakan |  | |
| fill_54 | พนกงานรฐวสาหกิจ | phanoknganonthawasahakit |  | |
| fill_12 | โทรศพท | sorotphot |  | |
| fill_13 | โทรสาร | thorsan |  | |
| fill_14 | เลขท | lekha |  | |
| fill_15 | ออกใหโดย | okhaidoi |  | |
| fill_16 | เมื่อ | muea |  | |
| fill_17 | หมดอาย | mot-ai |  | |
| comb_2 | โปรดระบเลขที่บตรประจาตวประชาชน | protraplekthibotprachatatatrachachon |  | |
| fill_18 | ๒.๑ ชื่อ | cocho chue |  | |
| fill_19 | สถานที่ตั้ง | sathanthitang |  | |
| fill_20 | ๒.๒ ทอย | cocho thoi |  | |
| fill_21 | โทรศพท | sorotphot |  | |
| fill_22 | โทรสาร | thorsan |  | |
| fill_23 | ๒.๓ อาชีพ | cocho achip |  | |
| fill_24 | สถานททางาน | sathantha-ngan |  | |
| fill_25 | โทรศพท | sorotphot |  | |
| fill_26 | กรณเปนนิติบคคลใหระบุลกษณะการประกอบการ [1] | koranapennitipkhonhairairairairairairairairairairairairairairairairairairairairairairairairairairair aa b |  | |
| fill_28 | กรณเปนนิติบคคลใหระบุลกษณะการประกอบการ [2] | koranapennitipkhonhairairairairairairairairairairairairairairairairairairairairairairairairairairair rako |  | |
| fill_59 | กรณเปนนิติบคคลใหระบุลกษณะการประกอบการ [3] | koranapennitipkhonhairairairairairairairairairairairairairairairairairairairairairairairairairairair aaho |  | |
| fill_58 | กรณเปนนิติบคคลใหระบุลกษณะการประกอบการ [4] | koranapennitipkhonhairairairairairairairairairairairairairairairairairairairairairairairairairairair aipa |  | |
| fill_57 | กรณเปนนิติบคคลใหระบุลกษณะการประกอบการ [5] | koranapennitipkhonhairairairairairairairairairairairairairairairairairairairairairairairairairairair ray |  | |
| fill_27 | ๒.๔ สถานทสะดวกในการตดต่อ | cocho sathanthasaduaknaikattotto |  | |
| fill_29 | โทรศพท | sorotphot |  | |
| fill_30 | โทรสาร | thorsan |  | |
| fill_31 | เลขท | lekha |  | |
| fill_32 | ออกใหโดย | okhaidoi |  | |
| fill_33 | เมื่อ | muea |  | |
| fill_34 | หมดอาย | mot-ai |  | |
| fill_35 | วนที่ทาธรกรรม | wonthithathonakam |  | |
| fill_36 | เดอน | doen |  | |
| fill_37 | พ.ศ | phosa | transaction_date_day | |
| fill_38 | ๓.๑ มลคาของธรกรรม | cocho monkhakhongthonakam | transaction_date_month | |
| fill_39 | โปรดระบุจานวนและสกลเงน | protrabuchanuanlaesakonnngngn | transaction_date_year | |
| fill_53 | (จานวนเงนทเปนตวอกษร) | phachanuanngentpentawekson |  | |
| fill_40 | ชอบญช | chopncha |  | |
| comb_3 | ชอเจาของบญช | chochaokhongboncha |  | |
| fill_42 | ชอบญช | chopncha |  | |
| comb_4 | ชอเจาของบญช | chochaokhongboncha |  | |
| fill_44 | เกยวของโดย [1] | koeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeo aa b |  | |
| fill_45 | เกยวของโดย [2] | koeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeoeo rako |  | |
| fill_46 | ๓.๕ ชอผู้รบประโยชนในการทาธรกรรม (ถาม | cocho chophuropprayotchonnaiaiathaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa phatham |  | |
| fill_47 | ๓.๖ วตถประสงคในการทาธรกรรม | cocho wottpharasongkhanaikanthathaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa |  | |
| fill_49 | เลขลาดบรายงาน | leklatbrai-ngan |  | |
| fill_50 | ๒ | a |  | |
| fill_14_2 | การรายงานทงหมดในชอง “รวมเอกสารจานวนทงสน | kanrai-nganthongmotnaichong ruam-ekkasanchanuanthongson |  | |
| fill_52 | สถาบนการเงิน | sathabonkanngoen |  | |
| Check Box61 |  |  |  | |
| Check Box62 |  |  |  | |
| Check Box63 |  |  |  | |
| Check Box64 |  |  |  | |
| Check Box65 |  |  |  | |
| Check Box66 |  |  |  | |
| Check Box67 |  |  |  | |
| Check Box68 |  |  |  | |
| Check Box69 |  |  |  | |
| Check Box70 |  |  |  | |
| Check Box71 |  |  |  | |
| Check Box72 |  |  |  | |
| Check Box73 |  |  |  | |
| Check Box74 |  |  |  | |
| Check Box75 |  |  |  | |
| Check Box76 |  |  |  | |
| Check Box77 |  |  |  | |
| Check Box78 |  |  |  | |
| t1 | [1] | aa b |  | |
| t2 | [2] | rako |  | |
| m_1 | [1] | aa b |  | |
| m_2 | [2] | rako |  | |
| m_3 | [3] | aaho |  | |
| m_4 | [4] | aipa |  | |
| m_5 | [5] | ray |  | |
| m_6 | [6] | oi-i |  | |
| m_7 | [7] | abo |  | |
| m_8 | [8] | aapo |  | |
| m_9 | [9] | ai |  | |
| m_10 | [10] | aiphopa |  | |
| m_11 | [11] | ro  a |  | |
| m_12 | [12] | ro  a |  | |
| m_13 | [13] | aiphoho |  | |
