#!/usr/bin/env python3
"""Merge Fatawa Razviya Jild 6 easy-Urdu tashreeh v4 chunks into jild-06.json.

Reads the 15 chunk files listed in chunks-manifest-v4-jild06.json,
concatenates them in order 01 -> 15, renames the second occurrence of
the duplicated masala number (see RENAME QUIRK below), derives
start_page = min(pages) where the field is absent, normalises page
markers, validates, and writes {"masail": [...]} to jild-06.json.

ORDER -- chunk order is the order (no quirk, unlike Jild 1 Part 2):
  The v3 merged file ~/workspace/fatawa-app/content/tashreeh/jild-06.json
  has ID order == concatenation order of the v4 chunks 01..15 (verified
  locally by the coordinator: all 400 ids match the v3 sequence exactly
  after the rename). Do NOT sort or reorder. Within each chunk, items
  keep file order.

RENAME QUIRK: the book numbers TWO different masail 774. The v3 merged
  file disambiguates the second occurrence by appending the start page:
  chunk-13 jild6-masala-774 (p. 611, "مسئلہ ۷۷۴ (بقیہ): بیوی کے بارے
  میں شکایت اور فاجرہ کو طلاق") -> jild6-masala-774-p611. The first
  occurrence stays plain (chunk-12, p. 610, "بیوی کے فسق پر راضی رہنے
  والا امام اور اس کے حامی"). The merge renames the SECOND occurrence
  of any duplicated id to {id}-p{start_page} and asserts exactly that
  one rename happens.

START_PAGE: every one of the 15 v4 chunks carries start_page ==
  min(pages) for all its items (verified by the coordinator). The
  derivation code below stays as a safety net; it is expected to
  derive 0 items.

MARKER NORMALISATION (the only text transformation): page markers, if
  present, are normalised to the single form [safha N] written with the
  Urdu word for page:
  - lenticular-bracket form (U+3010/U+3011 around the Urdu word for
    page + number) -> [safha N]
  - [short form] -> [safha N]
  - [safha N] stays as-is
  Applied to every string field of every item (jawab, sawal, title,
  notes). The 15 v4 chunks contain ZERO markers of any form (verified
  locally), so normalisation is expected to be a no-op here; the code
  stays so the merge is robust and the "none remain" assertions still
  run. No other text is touched and no markers are invented.
  NOTE: the literal lenticular-bracket characters are written here only
  as U+3010/U+3011 escapes, never as literal characters in this file.

VALIDATION (fails loudly on any violation):
  400 items; ID sequence EXACTLY == the v3 merged file's ID sequence
  (embedded below as V3_IDS, copied verbatim from
  ~/workspace/fatawa-app/content/tashreeh/jild-06.json); pages per item
  identical to v3 (embedded as V3_PAGES, same source, verified against
  the v3 file before pushing); 710 unique pages (min 5, max 736);
  volume_ids == {38}; start_page == min(pages) for every item (after
  derivation); zero empty tashreeh_jawab; no lenticular / short markers
  remain; first id jild6-p5, last id jild6-p723.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = "chunks-manifest-v4-jild06.json"

# Concatenation order: chunk files 01 -> 14, in order.
CHUNK_ORDER = [f"jild-06-chunk-{n:02d}.json" for n in range(1, 16)]

EXPECTED_ITEMS = 400
EXPECTED_PAGES = 710
EXPECTED_MIN_PAGE = 5
EXPECTED_MAX_PAGE = 736
EXPECTED_VOLUME_IDS = {38}
EXPECTED_FIRST_ID = "jild6-p5"
EXPECTED_LAST_ID = "jild6-p723"

# v3 ID sequence, verbatim from content/tashreeh/jild-06.json.
V3_IDS = ['jild6-p5', 'jild6-p6', 'jild6-p8', 'jild6-masala-389', 'jild6-masala-390', 'jild6-masala-391', 'jild6-masala-392', 'jild6-masala-393', 'jild6-masala-394', 'jild6-masala-395', 'jild6-masala-396', 'jild6-p63', 'jild6-p64', 'jild6-p66', 'jild6-p69', 'jild6-p71', 'jild6-p74', 'jild6-p76', 'jild6-p79', 'jild6-p83', 'jild6-p86', 'jild6-p91', 'jild6-p97', 'jild6-p102', 'jild6-p106', 'jild6-p110', 'jild6-p111', 'jild6-p115', 'jild6-p120', 'jild6-p125', 'jild6-masala-397', 'jild6-masala-398', 'jild6-masala-399', 'jild6-masala-400', 'jild6-masala-401', 'jild6-masala-402', 'jild6-masala-403', 'jild6-masala-404', 'jild6-masala-405', 'jild6-masala-406', 'jild6-p161', 'jild6-masala-407', 'jild6-masala-408', 'jild6-masala-409', 'jild6-masala-410', 'jild6-masala-411', 'jild6-masala-412', 'jild6-masala-413', 'jild6-masala-414', 'jild6-masala-418', 'jild6-masala-419', 'jild6-masala-420', 'jild6-masala-422', 'jild6-masala-425', 'jild6-masala-427', 'jild6-masala-428', 'jild6-masala-430', 'jild6-masala-431', 'jild6-masala-434', 'jild6-masala-435', 'jild6-masala-436', 'jild6-masala-438', 'jild6-masala-440', 'jild6-masala-441', 'jild6-masala-442', 'jild6-p211', 'jild6-masala-443', 'jild6-masala-444', 'jild6-masala-445', 'jild6-masala-446', 'jild6-masala-447', 'jild6-masala-448', 'jild6-masala-449', 'jild6-masala-450', 'jild6-masala-451', 'jild6-masala-452', 'jild6-masala-453', 'jild6-masala-454', 'jild6-masala-455', 'jild6-masala-456', 'jild6-masala-457', 'jild6-p261', 'jild6-masala-458', 'jild6-masala-459', 'jild6-masala-460', 'jild6-masala-461', 'jild6-masala-462', 'jild6-masala-463', 'jild6-masala-464', 'jild6-masala-465', 'jild6-masala-466', 'jild6-masala-467', 'jild6-masala-468', 'jild6-masala-469', 'jild6-masala-470', 'jild6-masala-471', 'jild6-masala-472', 'jild6-masala-477', 'jild6-p312', 'jild6-masala-478', 'jild6-masala-479', 'jild6-masala-480', 'jild6-masala-481', 'jild6-masala-482', 'jild6-masala-488', 'jild6-masala-489', 'jild6-masala-490', 'jild6-masala-491', 'jild6-masala-492', 'jild6-masala-495', 'jild6-masala-496', 'jild6-masala-497', 'jild6-masala-498', 'jild6-masala-499', 'jild6-masala-500', 'jild6-masala-501', 'jild6-masala-502', 'jild6-masala-503', 'jild6-masala-504', 'jild6-masala-505', 'jild6-masala-506', 'jild6-masala-507', 'jild6-masala-508', 'jild6-masala-509', 'jild6-masala-510', 'jild6-masala-511', 'jild6-masala-512', 'jild6-masala-513', 'jild6-masala-514', 'jild6-masala-516', 'jild6-masala-517', 'jild6-masala-518', 'jild6-masala-519', 'jild6-masala-520', 'jild6-masala-522', 'jild6-masala-523', 'jild6-masala-524', 'jild6-masala-525', 'jild6-masala-526', 'jild6-masala-527', 'jild6-masala-528', 'jild6-masala-529', 'jild6-masala-530', 'jild6-masala-531', 'jild6-masala-533', 'jild6-masala-535', 'jild6-masala-536', 'jild6-masala-537', 'jild6-masala-538', 'jild6-masala-539', 'jild6-masala-540', 'jild6-masala-541', 'jild6-masala-542', 'jild6-masala-543', 'jild6-p361', 'jild6-p363', 'jild6-p365', 'jild6-masala-555', 'jild6-masala-556', 'jild6-masala-559', 'jild6-masala-561', 'jild6-masala-563', 'jild6-p374', 'jild6-masala-564', 'jild6-masala-565', 'jild6-masala-567', 'jild6-masala-568', 'jild6-masala-569', 'jild6-masala-570', 'jild6-masala-571', 'jild6-masala-572', 'jild6-p386', 'jild6-masala-573', 'jild6-masala-574', 'jild6-masala-575', 'jild6-masala-576', 'jild6-masala-577', 'jild6-masala-578-579', 'jild6-masala-580', 'jild6-masala-581', 'jild6-masala-586', 'jild6-masala-583', 'jild6-p411', 'jild6-masala-584', 'jild6-masala-585-588', 'jild6-masala-589', 'jild6-masala-590', 'jild6-masala-591', 'jild6-masala-592', 'jild6-masala-593', 'jild6-masala-594', 'jild6-masala-595', 'jild6-masala-596', 'jild6-masala-597-599', 'jild6-masala-600', 'jild6-masala-601', 'jild6-masala-602', 'jild6-masala-603', 'jild6-masala-604', 'jild6-masala-605', 'jild6-masala-606', 'jild6-masala-607', 'jild6-masala-608', 'jild6-masala-609-612', 'jild6-masala-613', 'jild6-masala-614', 'jild6-masala-615', 'jild6-masala-616', 'jild6-masala-617', 'jild6-masala-618', 'jild6-masala-619', 'jild6-masala-620', 'jild6-masala-621', 'jild6-masala-622', 'jild6-masala-623', 'jild6-masala-624', 'jild6-masala-625-626', 'jild6-masala-627', 'jild6-masala-628', 'jild6-masala-629', 'jild6-masala-630', 'jild6-masala-631', 'jild6-masala-632', 'jild6-masala-633', 'jild6-masala-634', 'jild6-masala-635', 'jild6-masala-636', 'jild6-masala-637', 'jild6-masala-638', 'jild6-masala-639', 'jild6-masala-640', 'jild6-masala-641', 'jild6-masala-642', 'jild6-masala-643', 'jild6-masala-644', 'jild6-masala-651', 'jild6-masala-652', 'jild6-masala-653', 'jild6-masala-654', 'jild6-masala-655', 'jild6-masala-656', 'jild6-masala-657', 'jild6-masala-658', 'jild6-masala-659', 'jild6-masala-660', 'jild6-masala-661', 'jild6-masala-662', 'jild6-masala-663', 'jild6-masala-664', 'jild6-masala-665', 'jild6-masala-666', 'jild6-masala-667', 'jild6-masala-668', 'jild6-masala-675', 'jild6-masala-676', 'jild6-masala-677', 'jild6-masala-678', 'jild6-masala-679', 'jild6-masala-680', 'jild6-masala-681', 'jild6-masala-682', 'jild6-masala-684', 'jild6-masala-675b', 'jild6-masala-686', 'jild6-masala-687', 'jild6-masala-692-694', 'jild6-masala-695', 'jild6-masala-696', 'jild6-masala-697', 'jild6-masala-698', 'jild6-masala-699', 'jild6-masala-700', 'jild6-masala-701', 'jild6-masala-702', 'jild6-p561', 'jild6-masala-703', 'jild6-masala-704', 'jild6-masala-705', 'jild6-masala-706', 'jild6-masala-707', 'jild6-masala-711', 'jild6-masala-712', 'jild6-masala-713', 'jild6-masala-714', 'jild6-masala-715', 'jild6-masala-716', 'jild6-masala-717', 'jild6-masala-718', 'jild6-masala-719', 'jild6-masala-720', 'jild6-masala-721', 'jild6-masala-722', 'jild6-masala-723', 'jild6-masala-724', 'jild6-masala-727', 'jild6-masala-729', 'jild6-masala-735', 'jild6-masala-736', 'jild6-masala-737', 'jild6-masala-738', 'jild6-masala-739', 'jild6-masala-740', 'jild6-masala-741', 'jild6-masala-742', 'jild6-masala-743', 'jild6-masala-745', 'jild6-masala-748', 'jild6-masala-749', 'jild6-masala-750', 'jild6-masala-751', 'jild6-masala-753', 'jild6-masala-756', 'jild6-masala-758', 'jild6-masala-759', 'jild6-masala-760', 'jild6-masala-761', 'jild6-masala-763', 'jild6-masala-764', 'jild6-masala-765', 'jild6-masala-769', 'jild6-masala-771', 'jild6-masala-772', 'jild6-masala-773', 'jild6-masala-774', 'jild6-masala-774-p611', 'jild6-masala-775', 'jild6-masala-776', 'jild6-masala-777', 'jild6-masala-778', 'jild6-masala-785', 'jild6-masala-786', 'jild6-masala-787', 'jild6-masala-788', 'jild6-masala-789', 'jild6-masala-790', 'jild6-masala-791', 'jild6-masala-792', 'jild6-masala-795', 'jild6-masala-798', 'jild6-masala-799', 'jild6-masala-808', 'jild6-masala-809', 'jild6-masala-810', 'jild6-masala-811', 'jild6-masala-813', 'jild6-masala-814', 'jild6-masala-815', 'jild6-masala-816', 'jild6-masala-817', 'jild6-masala-818', 'jild6-masala-819', 'jild6-masala-820', 'jild6-masala-821', 'jild6-masala-822', 'jild6-masala-823', 'jild6-masala-824', 'jild6-masala-827', 'jild6-masala-828', 'jild6-masala-829', 'jild6-masala-830', 'jild6-masala-831', 'jild6-masala-832', 'jild6-p636', 'jild6-masala-833', 'jild6-masala-834', 'jild6-masala-835', 'jild6-masala-836', 'jild6-masala-837', 'jild6-masala-838', 'jild6-masala-839', 'jild6-masala-840', 'jild6-masala-841', 'jild6-masala-842', 'jild6-masala-843', 'jild6-masala-844', 'jild6-p648', 'jild6-masala-845', 'jild6-p657', 'jild6-p661', 'jild6-p663', 'jild6-p665', 'jild6-p668', 'jild6-p671', 'jild6-p675', 'jild6-p677', 'jild6-p681', 'jild6-p685', 'jild6-p687', 'jild6-p691', 'jild6-p693', 'jild6-p696', 'jild6-p702', 'jild6-p704', 'jild6-p711', 'jild6-p713', 'jild6-p716', 'jild6-p717', 'jild6-p719', 'jild6-p721', 'jild6-p723']

# v3 pages per item id, verbatim from content/tashreeh/jild-06.json.
V3_PAGES = {
"jild6-p5": [5],
"jild6-p6": [6, 7],
"jild6-p8": [8, 9, 10, 11, 12],
"jild6-masala-389": [29],
"jild6-masala-390": [29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39],
"jild6-masala-391": [39, 40, 41, 42, 43, 44, 45],
"jild6-masala-392": [46],
"jild6-masala-393": [46, 47, 48, 49, 50, 51, 52],
"jild6-masala-394": [53, 54, 55, 56, 57, 58],
"jild6-masala-395": [58, 59, 60],
"jild6-masala-396": [61, 62],
"jild6-p63": [63],
"jild6-p64": [64, 65],
"jild6-p66": [66, 67, 68],
"jild6-p69": [69, 70],
"jild6-p71": [71, 72, 73],
"jild6-p74": [74, 75],
"jild6-p76": [76, 77, 78],
"jild6-p79": [79, 80, 81, 82],
"jild6-p83": [83, 84, 85],
"jild6-p86": [86, 87, 88, 89, 90],
"jild6-p91": [91, 92, 93, 94, 95, 96],
"jild6-p97": [97, 98, 99, 100, 101],
"jild6-p102": [102, 103, 104, 105],
"jild6-p106": [106, 107, 108, 109],
"jild6-p110": [110],
"jild6-p111": [111, 112, 113, 114],
"jild6-p115": [115, 116, 117, 118, 119],
"jild6-p120": [120, 121, 122, 123, 124],
"jild6-p125": [125, 126, 127, 128, 129],
"jild6-masala-397": [130, 131, 132, 133, 134],
"jild6-masala-398": [135, 136, 137, 138, 139],
"jild6-masala-399": [140],
"jild6-masala-400": [141, 142, 143, 144, 145, 146],
"jild6-masala-401": [147, 148, 149, 150],
"jild6-masala-402": [151, 152],
"jild6-masala-403": [153, 154],
"jild6-masala-404": [155],
"jild6-masala-405": [156, 157, 158, 159],
"jild6-masala-406": [160],
"jild6-p161": [161],
"jild6-masala-407": [162, 163, 164, 165, 166],
"jild6-masala-408": [167, 168],
"jild6-masala-409": [169, 170, 171, 172, 173, 174, 175, 176],
"jild6-masala-410": [177, 178],
"jild6-masala-411": [179],
"jild6-masala-412": [180],
"jild6-masala-413": [181],
"jild6-masala-414": [182, 183, 184],
"jild6-masala-418": [185],
"jild6-masala-419": [186],
"jild6-masala-420": [187],
"jild6-masala-422": [188],
"jild6-masala-425": [189],
"jild6-masala-427": [190],
"jild6-masala-428": [191],
"jild6-masala-430": [192, 193, 194, 195, 196, 197, 198, 199],
"jild6-masala-431": [200],
"jild6-masala-434": [201],
"jild6-masala-435": [202],
"jild6-masala-436": [203],
"jild6-masala-438": [204],
"jild6-masala-440": [205],
"jild6-masala-441": [206],
"jild6-masala-442": [207, 208, 209, 210],
"jild6-p211": [211, 212, 213, 214, 215, 216, 217, 218],
"jild6-masala-443": [219],
"jild6-masala-444": [220],
"jild6-masala-445": [221],
"jild6-masala-446": [222, 223, 224, 225, 226, 227, 228, 229, 230],
"jild6-masala-447": [231],
"jild6-masala-448": [232],
"jild6-masala-449": [232],
"jild6-masala-450": [232, 233, 234, 235],
"jild6-masala-451": [235],
"jild6-masala-452": [236],
"jild6-masala-453": [237, 238, 239, 240, 241, 242, 243, 244],
"jild6-masala-454": [245, 246, 247],
"jild6-masala-455": [248, 249],
"jild6-masala-456": [250, 251, 252, 253, 254, 255, 256, 257],
"jild6-masala-457": [258, 259, 260],
"jild6-p261": [261, 262, 263],
"jild6-masala-458": [263, 264],
"jild6-masala-459": [264],
"jild6-masala-460": [264, 265],
"jild6-masala-461": [265, 266],
"jild6-masala-462": [266, 267],
"jild6-masala-463": [267, 268],
"jild6-masala-464": [268],
"jild6-masala-465": [268, 269],
"jild6-masala-466": [269, 270],
"jild6-masala-467": [269, 270, 271],
"jild6-masala-468": [271],
"jild6-masala-469": [271, 272],
"jild6-masala-470": [272],
"jild6-masala-471": [272, 273, 274, 275, 276, 277, 278, 279],
"jild6-masala-472": [280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298],
"jild6-masala-477": [299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310],
"jild6-p312": [312, 313, 314, 315, 316, 317, 318, 319],
"jild6-masala-478": [319, 320],
"jild6-masala-479": [320],
"jild6-masala-480": [320, 321, 322, 323],
"jild6-masala-481": [323, 324],
"jild6-masala-482": [324, 325],
"jild6-masala-488": [325, 326],
"jild6-masala-489": [326],
"jild6-masala-490": [326, 327, 328],
"jild6-masala-491": [328],
"jild6-masala-492": [328, 329],
"jild6-masala-495": [329, 330],
"jild6-masala-496": [330],
"jild6-masala-497": [330, 331],
"jild6-masala-498": [331],
"jild6-masala-499": [331, 332],
"jild6-masala-500": [332],
"jild6-masala-501": [333],
"jild6-masala-502": [333],
"jild6-masala-503": [333, 334, 335],
"jild6-masala-504": [335],
"jild6-masala-505": [335, 336],
"jild6-masala-506": [336],
"jild6-masala-507": [337],
"jild6-masala-508": [337, 338],
"jild6-masala-509": [338],
"jild6-masala-510": [338, 339],
"jild6-masala-511": [339, 340],
"jild6-masala-512": [340],
"jild6-masala-513": [340, 341],
"jild6-masala-514": [341],
"jild6-masala-516": [341, 342, 343],
"jild6-masala-517": [343],
"jild6-masala-518": [343, 344],
"jild6-masala-519": [344],
"jild6-masala-520": [344, 345],
"jild6-masala-522": [345],
"jild6-masala-523": [345],
"jild6-masala-524": [345, 346],
"jild6-masala-525": [346],
"jild6-masala-526": [346],
"jild6-masala-527": [346, 347],
"jild6-masala-528": [347],
"jild6-masala-529": [347, 348],
"jild6-masala-530": [348],
"jild6-masala-531": [348, 349],
"jild6-masala-533": [349],
"jild6-masala-535": [349, 350],
"jild6-masala-536": [349, 350],
"jild6-masala-537": [350],
"jild6-masala-538": [350, 351],
"jild6-masala-539": [350, 351],
"jild6-masala-540": [351, 352],
"jild6-masala-541": [352],
"jild6-masala-542": [352],
"jild6-masala-543": [352, 353, 354, 355, 356, 357, 358, 359, 360],
"jild6-p361": [361, 362],
"jild6-p363": [363, 364],
"jild6-p365": [365, 366],
"jild6-masala-555": [367],
"jild6-masala-556": [368],
"jild6-masala-559": [369],
"jild6-masala-561": [370],
"jild6-masala-563": [371, 372, 373],
"jild6-p374": [374, 375],
"jild6-masala-564": [376],
"jild6-masala-565": [377],
"jild6-masala-567": [378],
"jild6-masala-568": [379, 380],
"jild6-masala-569": [381],
"jild6-masala-570": [382],
"jild6-masala-571": [383, 384],
"jild6-masala-572": [385],
"jild6-p386": [386],
"jild6-masala-573": [387],
"jild6-masala-574": [387, 388],
"jild6-masala-575": [389],
"jild6-masala-576": [389, 390, 391, 392, 393],
"jild6-masala-577": [394],
"jild6-masala-578-579": [395, 396, 397, 398, 399],
"jild6-masala-580": [400, 401],
"jild6-masala-581": [402],
"jild6-masala-586": [403],
"jild6-masala-583": [404, 405, 406, 407, 408, 409, 410],
"jild6-p411": [411, 412],
"jild6-masala-584": [413, 414, 415],
"jild6-masala-585-588": [416, 417, 418],
"jild6-masala-589": [419],
"jild6-masala-590": [420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433],
"jild6-masala-591": [434, 435, 436],
"jild6-masala-592": [437, 438],
"jild6-masala-593": [439, 440],
"jild6-masala-594": [441, 442, 443, 444, 446, 447],
"jild6-masala-595": [448],
"jild6-masala-596": [448, 449],
"jild6-masala-597-599": [450, 451],
"jild6-masala-600": [452],
"jild6-masala-601": [453],
"jild6-masala-602": [454, 455],
"jild6-masala-603": [456],
"jild6-masala-604": [457],
"jild6-masala-605": [458],
"jild6-masala-606": [459],
"jild6-masala-607": [460],
"jild6-masala-608": [461, 462],
"jild6-masala-609-612": [463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475],
"jild6-masala-613": [475, 476, 477],
"jild6-masala-614": [477, 478],
"jild6-masala-615": [478, 479, 480, 481],
"jild6-masala-616": [481, 482],
"jild6-masala-617": [483, 484],
"jild6-masala-618": [484, 485],
"jild6-masala-619": [485, 486],
"jild6-masala-620": [486, 487],
"jild6-masala-621": [487, 488],
"jild6-masala-622": [488, 489, 490],
"jild6-masala-623": [490, 491, 492],
"jild6-masala-624": [492, 493],
"jild6-masala-625-626": [493],
"jild6-masala-627": [493, 494, 495, 496],
"jild6-masala-628": [496, 497],
"jild6-masala-629": [497, 499],
"jild6-masala-630": [499, 500],
"jild6-masala-631": [500, 501],
"jild6-masala-632": [501],
"jild6-masala-633": [501, 502],
"jild6-masala-634": [502],
"jild6-masala-635": [502, 503],
"jild6-masala-636": [503, 504, 505, 506, 508, 509],
"jild6-masala-637": [509],
"jild6-masala-638": [509, 510],
"jild6-masala-639": [510],
"jild6-masala-640": [510],
"jild6-masala-641": [511],
"jild6-masala-642": [512],
"jild6-masala-643": [512],
"jild6-masala-644": [512, 513, 514, 515, 516, 517, 518, 519, 520],
"jild6-masala-651": [520, 521],
"jild6-masala-652": [521],
"jild6-masala-653": [521, 522, 523],
"jild6-masala-654": [523],
"jild6-masala-655": [523, 524],
"jild6-masala-656": [525],
"jild6-masala-657": [525],
"jild6-masala-658": [525, 526],
"jild6-masala-659": [526, 527],
"jild6-masala-660": [527, 528, 529, 530, 531, 532, 533, 534],
"jild6-masala-661": [535],
"jild6-masala-662": [535],
"jild6-masala-663": [536],
"jild6-masala-664": [536, 537, 538],
"jild6-masala-665": [538, 539],
"jild6-masala-666": [539, 540, 541],
"jild6-masala-667": [541, 542],
"jild6-masala-668": [542, 543],
"jild6-masala-675": [544],
"jild6-masala-676": [544],
"jild6-masala-677": [544, 545],
"jild6-masala-678": [545],
"jild6-masala-679": [545],
"jild6-masala-680": [545, 546],
"jild6-masala-681": [546, 547],
"jild6-masala-682": [547],
"jild6-masala-684": [547, 548],
"jild6-masala-675b": [548],
"jild6-masala-686": [548, 549],
"jild6-masala-687": [550, 551, 552],
"jild6-masala-692-694": [552],
"jild6-masala-695": [552, 553],
"jild6-masala-696": [553],
"jild6-masala-697": [554, 555, 557],
"jild6-masala-698": [557, 558],
"jild6-masala-699": [558],
"jild6-masala-700": [558, 559],
"jild6-masala-701": [559],
"jild6-masala-702": [559, 560],
"jild6-p561": [561, 562],
"jild6-masala-703": [562, 563, 564, 565, 566, 567, 568, 569, 570, 571, 572],
"jild6-masala-704": [572],
"jild6-masala-705": [572, 573, 574],
"jild6-masala-706": [574],
"jild6-masala-707": [574, 576, 577],
"jild6-masala-711": [577],
"jild6-masala-712": [577],
"jild6-masala-713": [578],
"jild6-masala-714": [578, 579],
"jild6-masala-715": [579],
"jild6-masala-716": [579],
"jild6-masala-717": [579, 580, 581, 582],
"jild6-masala-718": [582],
"jild6-masala-719": [582, 583],
"jild6-masala-720": [583],
"jild6-masala-721": [584, 585],
"jild6-masala-722": [585, 586],
"jild6-masala-723": [586],
"jild6-masala-724": [586, 587],
"jild6-masala-727": [587, 588],
"jild6-masala-729": [588, 589],
"jild6-masala-735": [589],
"jild6-masala-736": [589, 590],
"jild6-masala-737": [590, 591],
"jild6-masala-738": [591, 592],
"jild6-masala-739": [592],
"jild6-masala-740": [592, 593, 594],
"jild6-masala-741": [594],
"jild6-masala-742": [594, 595, 596],
"jild6-masala-743": [596],
"jild6-masala-745": [596, 597],
"jild6-masala-748": [597],
"jild6-masala-749": [597, 598, 599],
"jild6-masala-750": [599, 600, 601],
"jild6-masala-751": [601, 602],
"jild6-masala-753": [602, 603],
"jild6-masala-756": [603],
"jild6-masala-758": [603, 604],
"jild6-masala-759": [604],
"jild6-masala-760": [604],
"jild6-masala-761": [604],
"jild6-masala-763": [604],
"jild6-masala-764": [604, 605],
"jild6-masala-765": [605, 606],
"jild6-masala-769": [606, 607],
"jild6-masala-771": [607],
"jild6-masala-772": [607, 608, 609],
"jild6-masala-773": [609, 610],
"jild6-masala-774": [610],
"jild6-masala-774-p611": [611],
"jild6-masala-775": [611, 612],
"jild6-masala-776": [612],
"jild6-masala-777": [612, 613],
"jild6-masala-778": [613, 614],
"jild6-masala-785": [614],
"jild6-masala-786": [614, 615],
"jild6-masala-787": [615],
"jild6-masala-788": [615, 616],
"jild6-masala-789": [616, 617],
"jild6-masala-790": [617, 618],
"jild6-masala-791": [618],
"jild6-masala-792": [618, 619],
"jild6-masala-795": [619, 620],
"jild6-masala-798": [620],
"jild6-masala-799": [620, 621, 622],
"jild6-masala-808": [622, 623],
"jild6-masala-809": [623],
"jild6-masala-810": [624],
"jild6-masala-811": [624, 625],
"jild6-masala-813": [624, 625],
"jild6-masala-814": [625, 626],
"jild6-masala-815": [626],
"jild6-masala-816": [626, 627],
"jild6-masala-817": [627],
"jild6-masala-818": [628],
"jild6-masala-819": [628],
"jild6-masala-820": [628],
"jild6-masala-821": [628, 629],
"jild6-masala-822": [629, 630],
"jild6-masala-823": [630],
"jild6-masala-824": [630, 631, 632],
"jild6-masala-827": [632],
"jild6-masala-828": [632, 633],
"jild6-masala-829": [633, 634],
"jild6-masala-830": [634],
"jild6-masala-831": [634, 635],
"jild6-masala-832": [635],
"jild6-p636": [636],
"jild6-masala-833": [636],
"jild6-masala-834": [636, 637],
"jild6-masala-835": [637, 638],
"jild6-masala-836": [638, 639],
"jild6-masala-837": [639, 640],
"jild6-masala-838": [640, 641],
"jild6-masala-839": [641],
"jild6-masala-840": [641],
"jild6-masala-841": [642],
"jild6-masala-842": [642],
"jild6-masala-843": [642, 643],
"jild6-masala-844": [643, 644, 645, 646, 647],
"jild6-p648": [648, 649],
"jild6-masala-845": [649, 650, 651, 652, 653, 654, 655, 656, 657],
"jild6-p657": [657, 658, 659, 660],
"jild6-p661": [661, 662],
"jild6-p663": [663, 664],
"jild6-p665": [665, 666, 667],
"jild6-p668": [668, 669, 670],
"jild6-p671": [671, 672, 673, 674],
"jild6-p675": [675, 676],
"jild6-p677": [677, 678, 679, 680],
"jild6-p681": [681, 682, 683, 684],
"jild6-p685": [685, 686],
"jild6-p687": [687, 688, 689, 690],
"jild6-p691": [691, 692],
"jild6-p693": [693, 694, 695],
"jild6-p696": [696, 697, 698, 699, 700, 701],
"jild6-p702": [702, 703],
"jild6-p704": [704, 705, 706, 707, 708, 709, 710],
"jild6-p711": [711, 712],
"jild6-p713": [713, 714, 715],
"jild6-p716": [716],
"jild6-p717": [717, 718],
"jild6-p719": [719, 720],
"jild6-p721": [721, 722],
"jild6-p723": [723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 735, 736],
}

# The Urdu word for "page" is safha; the canonical marker is [safha N].
# Lenticular brackets are U+3010 (open) and U+3011 (close); the short
# form is "[safha-initial N]" with the single-letter abbreviation.
# All three patterns are built from escapes so this file never contains
# a literal lenticular-bracket pair.
SAFHA = "\u0635\u0641\u062d\u06c1"  # the Urdu word for page
RE_LENTICULAR = re.compile("\u3010" + SAFHA + " (\\d+)\u3011")
RE_SHORT = re.compile("\\[\u0635 (\\d+)\\]")
RE_FULL = re.compile("\\[" + SAFHA + " \\d+\\]")
LENTICULAR_PREFIX = "\u3010" + SAFHA  # for the "none remain" check
SHORT_PREFIX_RE = re.compile("\\[\u0635 \\d+\\]")

# Canonical output key order for every item (the JSON contract).
ITEM_KEYS = ["id", "title", "volume_id", "pages", "start_page",
             "tashreeh_sawal", "tashreeh_jawab", "notes"]


def normalise_markers(text):
    """Normalise page markers in one string. Returns (new_text, counts)."""
    counts = {"lenticular": 0, "short": 0, "full_before": 0}
    counts["full_before"] = len(RE_FULL.findall(text))
    text, n1 = RE_LENTICULAR.subn("[" + SAFHA + " \\1]", text)
    counts["lenticular"] = n1
    text, n2 = RE_SHORT.subn("[" + SAFHA + " \\1]", text)
    counts["short"] = n2
    return text, counts


def normalise_item(item):
    """Normalise markers in every string field of one item (recursively
    through lists/dicts). Returns per-form counts for this item."""
    totals = {"lenticular": 0, "short": 0, "full_before": 0}

    def walk(value):
        if isinstance(value, str):
            new, c = normalise_markers(value)
            for k in totals:
                totals[k] += c[k]
            return new
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        return value

    for key in list(item.keys()):
        item[key] = walk(item[key])
    return totals


def main():
    assert len(V3_IDS) == EXPECTED_ITEMS, "embedded V3_IDS length mismatch"
    assert set(V3_PAGES) == set(V3_IDS), "embedded V3_PAGES keys != V3_IDS"
    assert sum(len(v) for v in V3_PAGES.values()) >= EXPECTED_PAGES

    manifest = json.load(open(os.path.join(BASE, MANIFEST), encoding="utf-8"))
    entries = manifest["chunks"]
    assert len(entries) == 15, f"expected 14 manifest entries, got {len(entries)}"
    assert all(e.get("status") == "done" for e in entries), "not all chunks done"
    by_file = {e["file"]: e for e in entries}
    assert set(by_file) == set(CHUNK_ORDER), (
        f"manifest files != CHUNK_ORDER: "
        f"missing={set(CHUNK_ORDER) - set(by_file)} "
        f"extra={set(by_file) - set(CHUNK_ORDER)}"
    )

    all_items = []
    derived = []
    for fname in CHUNK_ORDER:
        path = os.path.join(BASE, fname)
        d = json.load(open(path, encoding="utf-8"))
        items = d["masail"]
        entry = by_file[fname]
        assert len(items) == entry["items"], (
            f"{fname}: {len(items)} items, manifest says {entry['items']}"
        )
        # Marker normalisation, with before/after counts per chunk.
        before = {"lenticular": 0, "short": 0, "full_before": 0}
        for it in items:
            c = normalise_item(it)
            for k in before:
                before[k] += c[k]
        after_full = sum(
            len(RE_FULL.findall(json.dumps(it, ensure_ascii=False)))
            for it in items
        )
        print(
            f"{fname}: {len(items)} items | markers before: "
            f"lenticular={before['lenticular']} short={before['short']} "
            f"full={before['full_before']} | after: full={after_full}"
        )
        assert after_full == (
            before["lenticular"] + before["short"] + before["full_before"]
        ), f"{fname}: marker count changed by normalisation!"
        # Derive start_page = min(pages) where absent (chunks 06, 12).
        for it in items:
            if "start_page" not in it:
                it["start_page"] = min(it["pages"])
                derived.append(it["id"])
        all_items.extend(items)

    # RENAME QUIRK (Jild 6 only): the book numbers TWO different masail
    # 774. The chunk files use the plain id for both occurrences; the
    # v3 merged file disambiguates the second occurrence by appending
    # the start page. Rename the SECOND occurrence of any duplicated id
    # to {id}-p{start_page}.
    seen_ids = set()
    renamed = []
    for it in all_items:
        if it["id"] in seen_ids:
            new_id = f"{it['id']}-p{min(it['pages'])}"
            renamed.append((it["id"], new_id))
            it["id"] = new_id
        seen_ids.add(it["id"])
    print(f"renames applied: {renamed}")
    assert renamed == [("jild6-masala-774", "jild6-masala-774-p611")], (
        f"unexpected renames: {renamed}"
    )

    print(f"concatenated: {len(all_items)} items")
    print(f"start_page derived for {len(derived)} items (expected 0: all chunks carry start_page)")
    assert len(all_items) == EXPECTED_ITEMS, (
        f"expected {EXPECTED_ITEMS} items, got {len(all_items)}"
    )

    # Rebuild each item in the canonical key order (the JSON contract).
    canonical = []
    for it in all_items:
        assert set(it.keys()) == set(ITEM_KEYS), (
            f"{it.get('id')}: keys {sorted(it.keys())} != {sorted(ITEM_KEYS)}"
        )
        canonical.append({k: it[k] for k in ITEM_KEYS})
    all_items = canonical

    # Validation.
    ids = [it["id"] for it in all_items]
    assert ids == V3_IDS, (
        f"ID sequence != v3: first diff at "
        f"{next((i for i, (a, b) in enumerate(zip(ids, V3_IDS)) if a != b), min(len(ids), len(V3_IDS)))}"
    )
    assert len(ids) == len(set(ids)), (
        f"DUPLICATE IDS: {[i for i in ids if ids.count(i) > 1]}"
    )
    empty = [it["id"] for it in all_items if not it.get("tashreeh_jawab")]
    assert not empty, f"EMPTY JAWAB: {empty}"
    vols = set(it.get("volume_id") for it in all_items)
    assert vols == EXPECTED_VOLUME_IDS, f"volume_ids {vols} != {EXPECTED_VOLUME_IDS}"
    pages = set()
    for it in all_items:
        assert it["pages"] == V3_PAGES[it["id"]], (
            f"{it['id']}: pages {it['pages']} != v3 {V3_PAGES[it['id']]}"
        )
        pages.update(it["pages"])
    assert len(pages) == EXPECTED_PAGES, (
        f"expected {EXPECTED_PAGES} unique pages, got {len(pages)}"
    )
    assert min(pages) == EXPECTED_MIN_PAGE, f"min page {min(pages)}"
    assert max(pages) == EXPECTED_MAX_PAGE, f"max page {max(pages)}"
    exceptions = {
        it["id"] for it in all_items if it["start_page"] != min(it["pages"])
    }
    assert not exceptions, f"start_page != min(pages): {sorted(exceptions)}"
    assert ids[0] == EXPECTED_FIRST_ID, f"first id {ids[0]}"
    assert ids[-1] == EXPECTED_LAST_ID, f"last id {ids[-1]}"

    out = {"masail": all_items}
    out_text = json.dumps(out, ensure_ascii=False, indent=1)
    assert LENTICULAR_PREFIX not in out_text, "lenticular markers remain in output!"
    assert not SHORT_PREFIX_RE.search(out_text), "short markers remain in output!"
    total_markers = len(RE_FULL.findall(out_text))
    print(
        f"VALIDATION PASSED: {len(all_items)} items, {len(pages)} unique pages "
        f"(min {min(pages)}, max {max(pages)}), volume_ids {sorted(vols)}, "
        f"first {ids[0]}, last {ids[-1]}, start_page == min(pages) for all, "
        f"derived start_page for {len(derived)} items, markers {total_markers}"
    )

    with open(os.path.join(BASE, "jild-06.json"), "w", encoding="utf-8") as f:
        f.write(out_text)
    print(f"WROTE jild-06.json: {len(out_text.encode('utf-8'))} bytes")


if __name__ == "__main__":
    main()
