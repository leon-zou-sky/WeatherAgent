"""
AQI 数据下载器（简化版）
从在意空气（Air Matters）API获取AQI数据

用法:
    python -m downloader.aqi_downloader              # 下载所有城市AQI
    python -m downloader.aqi_downloader --city 北京   # 下载指定城市AQI
    python -m downloader.aqi_downloader --list        # 列出支持的城市
"""

import argparse
import contextlib
import json
import logging
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

from downloader.models import AQICity, AQIStation, create_tables, get_engine, get_session

# 加载环境变量
load_dotenv(Path(__file__).resolve().parent.parent / ".env.example")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ============ 城市映射 ============
# 在意空气城市ID -> (城市名, 系统城市ID)
# 系统城市ID用于与其他数据表关联

CITY_MAPPING = {
    "ace4d457": ("七台河", "101051002"),
    "fe0200a7": ("万宁", "101310215"),
    "bc601f80": ("三亚", "101310201"),
    "d9164119": ("三明", "101230801"),
    "3f5bde2f": ("三门峡", "101181701"),
    "90868c5d": ("上海", "101020100"),
    "c2ab274d": ("上饶", "101240301"),
    "aa1376ab": ("东区", "101270205"),
    "35833194": ("东方", "101310202"),
    "950e3410": ("东莞", "101281601"),
    "c84e975f": ("东营", "101121299"),
    "a7aa96f8": ("中卫", "101170501"),
    "aa3922c0": ("中山", "101070208"),
    "8d4e6fbc": ("中西区", "101270206"),
    "6e2400b6": ("临夏州", "101161101"),
    "9fc5e670": ("临安", "101210107"),
    "5a25b2b3": ("临汾", "101100701"),
    "c4771a1e": ("临沂", "101120901"),
    "e6bb400c": ("临沧", "101291101"),
    "c7940be1": ("临高", "101310203"),
    "f1991190": ("丹东", "101070601"),
    "2cbea3e9": ("丽水", "101210801"),
    "12c30d1c": ("丽江", "101291401"),
    "2c27e392": ("义乌", "101210904"),
    "4004d65c": ("乌兰察布", "101080405"),
    "c5654517": ("乌兰浩特市", "101081101"),
    "87cf4073": ("乌海", "101080301"),
    "e7d9c1ba": ("乌鲁木齐", "101130113"),
    "5fb581c5": ("乐东", "101310221"),
    "94d258e8": ("乐山", "101271401"),
    "0ce77078": ("乐都区", "101150202"),
    "65857c35": ("九江", "101240201"),
    "bdcd4251": ("九龙", "101320102"),
    "b3dd69c1": ("乳山", "101121304"),
    "ee40d9c9": ("云林县", "101340406"),
    "0b0d55a9": ("云浮", "101281401"),
    "5fd07bf9": ("五家渠", "101131801"),
    "2f0ece4e": ("五指山", "101310222"),
    "a624e018": ("亳州", "101220901"),
    "06f3e0bc": ("仙桃", "101201601"),
    "776d2647": ("伊春", "101050899"),
    "34fb412c": ("伊犁哈萨克州", "101131012"),
    "1098bd36": ("佛坪县", "101110808"),
    "0b046ff4": ("佛山", "101280800"),
    "672255db": ("佳木斯", "101050401"),
    "85902a53": ("保亭黎族苗族自治县", "101310214"),
    "86ac8491": ("保定", "101090201"),
    "39b7aae3": ("保山", "101290501"),
    "89a2162d": ("信阳", "101180601"),
    "8a45e457": ("克拉玛依", "101130299"),
    "7b91f57a": ("六安", "101221501"),
    "d6b00e0f": ("六盘水", "101260803"),
    "88a69c6a": ("兰州", "101160101"),
    "691030fb": ("兴安盟", "101081199"),
    "8e096673": ("内江", "101271201"),
    "258d76f1": ("凉山州", "101271601"),
    "c48299bc": ("包头", "101080201"),
    "ec8399ca": ("北京", "101010100"),
    "c7774e36": ("北海", "101301301"),
    "5ca8aa55": ("十堰", "101201101"),
    "61a2741f": ("南京", "101190101"),
    "1bfe3ad0": ("南充", "101270501"),
    "9ffdc266": ("南宁", "101300101"),
    "c48b8def": ("南平", "101230901"),
    "b87143e9": ("南投", "101340404"),
    "66b2f51c": ("南昌", "101240101"),
    "370012b7": ("南通", "101190501"),
    "faffcc99": ("南阳", "101180701"),
    "44ff94d3": ("即墨", "101120204"),
    "05e6d64f": ("厦门", "101230201"),
    "c7e3e9d5": ("双河市", "101131412"),
    "dc6c68ab": ("双鸭山", "101051301"),
    "5ae9a787": ("古蔺县", "101271006"),
    "41511fc4": ("句容", "101190304"),
    "c0e05355": ("台东", "101340204"),
    "ed4d93e2": ("台中", "101340401"),
    "c1d0ba27": ("台北市", "101340101"),
    "873314a8": ("台州", "101210601"),
    "7a2d19bf": ("合肥", "101220101"),
    "99a50dba": ("吉安", "101240601"),
    "00efff91": ("吉林", "101060201"),
    "ca06235a": ("吐鲁番", "101130501"),
    "fae7f790": ("吕梁", "101101100"),
    "fde73580": ("吴忠", "101170301"),
    "093850f3": ("吴江", "101190407"),
    "6893082d": ("周口", "101181401"),
    "894835e7": ("呼伦贝尔", "101081013"),
    "b02d732c": ("呼和浩特", "101080101"),
    "61ec191e": ("和田", "101131301"),
    "4bf4e6d4": ("咸宁", "101200701"),
    "2beecb4e": ("咸阳", "101110200"),
    "44b14b06": ("哈密", "101131201"),
    "e31e2051": ("哈尔滨", "101050101"),
    "3ae8ec3b": ("唐山", "101090501"),
    "a533f341": ("商丘", "101181001"),
    "8cc7ed22": ("商洛", "101110601"),
    "0388ced1": ("喀什", "101130901"),
    "7418bb74": ("嘉义", "101340202"),
    "a45bef13": ("嘉义县", "101070704"),
    "b89c28d1": ("嘉兴", "101210301"),
    "2efdc87e": ("嘉峪关", "101161401"),
    "c146d993": ("四平", "101060401"),
    "2c660585": ("固原", "101170401"),
    "7f267533": ("基隆", "101340109"),
    "eb7463ff": ("基隆市", "101340109"),
    "d76afc14": ("塔城", "101131101"),
    "59c71751": ("大兴安岭", "101050701"),
    "8d646dcd": ("大同", "101050910"),
    "b792a6a1": ("大埔区", "101280404"),
    "ae681788": ("大庆", "101050901"),
    "1b9b66a4": ("大理州", "101290201"),
    "f068d4ce": ("大连", "101070201"),
    "dd3334bb": ("天水", "101160901"),
    "429fc25c": ("天津", "101030100"),
    "509171c1": ("天门", "101201501"),
    "0c611a9e": ("太仓", "101190408"),
    "fa9deebc": ("太原", "101100101"),
    "66a8da44": ("威海", "101121301"),
    "5c3ccd92": ("娄底", "101250801"),
    "36fff1fb": ("孝感", "101200401"),
    "d07155ac": ("宁德", "101230301"),
    "7bad216e": ("宁波", "101210401"),
    "3b4a24da": ("安庆", "101220601"),
    "84f89682": ("安康", "101110701"),
    "8ffcb0eb": ("安阳", "101180299"),
    "4d7811d2": ("安顺", "101260301"),
    "37668a32": ("定安", "101310209"),
    "8059ce9d": ("定西", "101160201"),
    "9d42496f": ("宜兰", "101340104"),
    "e4ba6405": ("宜兴", "101190203"),
    "be06bfdd": ("宜宾", "101271101"),
    "3660461c": ("宜昌", "101200901"),
    "378d89ce": ("宜春", "101240501"),
    "8c6b74f1": ("宝鸡", "101110901"),
    "0395e07d": ("宣城", "101221401"),
    "6af4314e": ("宿州", "101220701"),
    "a6519af9": ("宿迁", "101191301"),
    "732c615c": ("富阳", "101210108"),
    "47e97636": ("寿光", "101120603"),
    "0928d406": ("屏东", "101340205"),
    "5106f603": ("屯昌", "101310210"),
    "0f997a5e": ("山南", "101140301"),
    "72739c97": ("岳阳", "101251099"),
    "231d1a9d": ("崇左", "101300201"),
    "a71dafe9": ("巴中", "101270901"),
    "c300491c": ("巴彦淖尔", "101080811"),
    "68460fb4": ("常州", "101191101"),
    "caebc6e8": ("常德", "101250601"),
    "0601445b": ("常熟", "101190402"),
    "152b8bd3": ("平凉", "101160301"),
    "306c8340": ("平安区", "101150208"),
    "0923717b": ("平顶山", "101180501"),
    "30bab85c": ("广元", "101272101"),
    "ae4625d8": ("广安", "101270899"),
    "6f6d028c": ("广州", "101280101"),
    "d3392211": ("庆阳", "101160401"),
    "0e49feb5": ("库尔勒", "101130601"),
    "17bc7c51": ("廊坊", "101090601"),
    "60deb04a": ("延安", "101110300"),
    "ebc99ba9": ("延边州", "101060306"),
    "7fc5f703": ("开封", "101180801"),
    "17d06691": ("张家口", "101090301"),
    "59c90a8b": ("张家港", "101190403"),
    "69297f48": ("张家界", "101251101"),
    "5a8d22de": ("张掖", "101160701"),
    "f291f9bc": ("彰化", "101340403"),
    "2bb9cffc": ("徐州", "101190801"),
    "32351fba": ("德宏州", "101291501"),
    "f6058131": ("德州", "101120401"),
    "a1aaa4e0": ("德阳", "101272001"),
    "899fc37b": ("忻州", "101101001"),
    "74d88b80": ("怀化", "101251201"),
    "f48b39cb": ("怒江州", "101291201"),
    "6c70a55a": ("恩施州", "101201001"),
    "48d50eb1": ("惠州", "101280301"),
    "0c566d27": ("成都", "101270101"),
    "dc078314": ("扎赉特旗", "101081105"),
    "d3722a11": ("扬州", "101190601"),
    "5cfd7e11": ("承德", "101090402"),
    "3d8074ad": ("抚州", "101240401"),
    "826669be": ("抚顺", "101070401"),
    "c6ca807d": ("拉萨", "101140101"),
    "3babe74e": ("招远", "101120506"),
    "b5a2f3c6": ("揭阳", "101281901"),
    "3434ffdc": ("攀枝花", "101270201"),
    "c1645fa3": ("文山州", "101290601"),
    "9350ba0a": ("文登", "101121302"),
    "45938318": ("新乡", "101180399"),
    "dbf32123": ("新余", "101241001"),
    "649a546c": ("新北", "101340108"),
    "6ef539df": ("新源县", "101131006"),
    "cfd250a8": ("新界", "101320103"),
    "882cfb57": ("新竹", "101340103"),
    "097b6899": ("新竹县", "101340103"),
    "ea22ab01": ("无锡", "101190201"),
    "d00792d1": ("日喀则", "101140201"),
    "c540cbaf": ("日照", "101121501"),
    "7f140494": ("昆山", "101190404"),
    "f3e7a2e6": ("昆明", "101290101"),
    "2e6e1d6f": ("昌吉州", "101130401"),
    "de8c1e8d": ("昌邑市", "101060207"),
    "04a37558": ("昌都", "101140501"),
    "18cef803": ("昭通", "101291001"),
    "f2ee84d1": ("晋中", "101100401"),
    "c5327be2": ("晋城", "101100601"),
    "3fb4c63b": ("普洱", "101290901"),
    "1e2216fb": ("景德镇", "101240801"),
    "f7b15057": ("曲靖", "101290401"),
    "5a629768": ("朔州", "101100901"),
    "1d21bee7": ("朝阳", "101060110"),
    "a58d2125": ("本溪", "101070501"),
    "21b97f34": ("来宾", "101300401"),
    "050dbfc4": ("杭州", "101210101"),
    "4e29e23d": ("松原", "101060801"),
    "e635f8c9": ("林芝", "101140401"),
    "370f261a": ("果洛州", "101150501"),
    "41568472": ("枣庄", "101121401"),
    "895e41ea": ("柳州", "101300301"),
    "cc78b294": ("株洲", "101250301"),
    "a3e774b9": ("桂林", "101300501"),
    "e7b693b4": ("桃园", "101340102"),
    "c57d06d4": ("梅州", "101280401"),
    "f3d69c64": ("梧州", "101300601"),
    "6590eca8": ("楚雄州", "101290801"),
    "4ab67887": ("榆林", "101110401"),
    "7d95a6bf": ("武威", "101160501"),
    "5859ec92": ("武宁县", "101160407"),
    "4249d4e3": ("武汉", "101200101"),
    "35cc1453": ("武都区", "101161001"),
    "79955b83": ("毕节", "101260701"),
    "9303fb09": ("永州", "101251401"),
    "7dcec15b": ("汉中", "101110801"),
    "e614c9a1": ("汕头", "101280501"),
    "1960db66": ("汕尾", "101282101"),
    "20ebe629": ("江门", "101281101"),
    "974b18ea": ("江阴", "101190202"),
    "3e716c57": ("池州", "101221701"),
    "ff5cfdb9": ("沈阳", "101070101"),
    "bee5bfaa": ("沧州", "101090701"),
    "da63486a": ("河池", "101301201"),
    "7ab3b260": ("河源", "101281201"),
    "019bf26a": ("泉州", "101230501"),
    "f850feac": ("泰安", "101120801"),
    "080c32d8": ("泰州", "101191201"),
    "7cbe927d": ("泸州", "101271001"),
    "04ab60fe": ("洛阳", "101180901"),
    "e13464dc": ("济南", "101120101"),
    "96a43c90": ("济宁", "101120701"),
    "7559f652": ("济源市", "101181801"),
    "4da56111": ("海东", "101150201"),
    "e1014aa6": ("海北州", "101150801"),
    "a8be8bf1": ("海南州", "101080303"),
    "71ab5299": ("海口", "101310101"),
    "16dda84f": ("海西州", "101150701"),
    "f495f559": ("海门", "101190508"),
    "a4284025": ("淄博", "101120301"),
    "c7627feb": ("淮北", "101221201"),
    "21f7deee": ("淮南", "101220401"),
    "e5f594eb": ("淮安", "101190901"),
    "0c8c7e67": ("深圳", "101280601"),
    "c98aab61": ("清远", "101281301"),
    "4d99333d": ("温州", "101210701"),
    "f6367e27": ("渭南", "101110501"),
    "7befe414": ("湖州", "101210201"),
    "ac0074cc": ("湘潭", "101250299"),
    "ea87063f": ("湘西州", "101251509"),
    "738b8aad": ("湛江", "101281001"),
    "160133d0": ("溧阳", "101191102"),
    "36d3cee9": ("滁州", "101221101"),
    "68ca6993": ("滨州", "101121101"),
    "144ffbca": ("漯河", "101181501"),
    "d0104097": ("漳州", "101230601"),
    "3f00c10b": ("潍坊", "101120601"),
    "32e8ea6d": ("潜江", "101201701"),
    "b97b84d6": ("潮州", "101281501"),
    "e4f65060": ("澄迈", "101310204"),
    "f6df2af6": ("澎湖县", "101340407"),
    "1212a003": ("澳门", "101330101"),
    "7ede3518": ("濮阳", "101181399"),
    "6d5fd7ee": ("烟台", "101120501"),
    "7846b63b": ("焦作", "101181101"),
    "797aab6f": ("牡丹江", "101050301"),
    "37e3c301": ("特克斯县", "101131008"),
    "cc5f6852": ("玉林", "101300901"),
    "3cd52690": ("玉树州", "101150601"),
    "e761f3b5": ("玉溪", "101290701"),
    "5640a1bb": ("珠海", "101280701"),
    "b79199bd": ("琼中", "101310208"),
    "a562d238": ("琼海", "101310211"),
    "6ab6bd2e": ("瓦房店", "101070202"),
    "0c94cfd0": ("甘南州", "101161209"),
    "20d7410b": ("甘孜州", "101271801"),
    "42e62406": ("白城", "101060601"),
    "a4998cd1": ("白山", "101060901"),
    "037ed067": ("白银", "101161399"),
    "4ee46bb9": ("百色", "101301001"),
    "33caec1b": ("益阳", "101250700"),
    "e6a425b0": ("盐城", "101190701"),
    "04f4bf7e": ("盘锦", "101071301"),
    "80aa2a4c": ("眉山", "101271501"),
    "36b5cdf8": ("石嘴山", "101170201"),
    "1e690e01": ("石家庄", "101090101"),
    "4c918731": ("石河子", "101130301"),
    "8b0f8d8e": ("神农架林区", "101201201"),
    "3992b627": ("福州", "101230101"),
    "aeba0ad4": ("秦皇岛", "101091101"),
    "1a44358a": ("章丘", "101120104"),
    "216b54c4": ("红河州", "101290301"),
    "c7c5695a": ("绍兴", "101210507"),
    "77473d2c": ("绥化", "101050501"),
    "d66196e7": ("绵阳", "101270401"),
    "76f84ce3": ("聊城", "101121701"),
    "a3b87f28": ("肇庆", "101280901"),
    "92d0c921": ("胶州", "101120205"),
    "39032161": ("自贡", "101270301"),
    "ec7ca242": ("舟山", "101211101"),
    "45f2a0ee": ("芜湖", "101220301"),
    "e6cb9277": ("花莲", "101340405"),
    "342109d9": ("苏州", "101190401"),
    "995f7a4c": ("苗栗", "101340402"),
    "70051ec7": ("茂名", "101282001"),
    "9e6ef19d": ("荆州", "101200899"),
    "15b8f5bb": ("荆门", "101201401"),
    "fbc6e749": ("荣成", "101121303"),
    "dc230b1d": ("莆田", "101230401"),
    "b3095f6a": ("莱州", "101120502"),
    "674cc22d": ("莱芜", "101121602"),
    "462f5c38": ("莱西", "101120207"),
    "9a6560ea": ("菏泽", "101121001"),
    "258ba6c6": ("萍乡", "101240901"),
    "e417178f": ("营口", "101070801"),
    "8dcae4c8": ("葫芦岛", "101071401"),
    "67128072": ("蓬莱", "101120504"),
    "285f9cd2": ("蚌埠", "101220201"),
    "34e778a4": ("衡水", "101090801"),
    "c80490ff": ("衡阳", "101250401"),
    "8a93143f": ("衢州", "101211001"),
    "97eb4c67": ("襄阳", "101200201"),
    "ad8f1ce1": ("西双版纳州", "101291602"),
    "ac2ef3be": ("西宁", "101150101"),
    "88f54f06": ("西安", "101060705"),
    "3b075bd2": ("许昌", "101180401"),
    "c186dd76": ("诸暨", "101210502"),
    "f33b3d20": ("贵港", "101300801"),
    "6bab735b": ("贵阳", "101260101"),
    "f77e21ce": ("贺州", "101300701"),
    "5ee2d2dd": ("资阳", "101250706"),
    "8c075a5a": ("赣州", "101240701"),
    "16b1a239": ("赤峰", "101080601"),
    "ed2ecf71": ("辽源", "101060701"),
    "f1719690": ("辽阳", "101071001"),
    "affd1f44": ("达州", "101270601"),
    "f9098c5b": ("运城", "101100801"),
    "7649868a": ("连云港", "101191001"),
    "8b9bf6d6": ("连江县", "101230105"),
    "edcfeb5f": ("迪庆州", "101291305"),
    "8dc5a772": ("通化", "101060501"),
    "5776d12c": ("通辽", "101080501"),
    "a553d23a": ("遂宁", "101270701"),
    "1e2d71d4": ("遵义", "101260201"),
    "f308dfcf": ("邢台", "101090999"),
    "47ac265b": ("那曲", "101140601"),
    "103ae33f": ("邯郸", "101091001"),
    "193ab0e8": ("邵阳", "101250901"),
    "5b687f00": ("郑州", "101180101"),
    "aaa44753": ("郴州", "101250501"),
    "e9326dd3": ("鄂尔多斯", "101080701"),
    "4a230484": ("鄂州", "101200301"),
    "8d49f424": ("酒泉", "101160801"),
    "e8cafa50": ("重庆", "101040100"),
    "39080ea6": ("金华", "101210901"),
    "fb7fe796": ("金坛", "101191103"),
    "994f4f25": ("金昌", "101160601"),
    "6db0e745": ("金门县", "101230503"),
    "7825c4ee": ("钦州", "101301101"),
    "1e4228f6": ("铁岭", "101071101"),
    "0c288183": ("铜仁", "101260601"),
    "97c5a6dc": ("铜川", "101111001"),
    "ad89931c": ("铜陵", "101221301"),
    "dde59501": ("银川", "101170101"),
    "98f9da6f": ("锡林郭勒盟", "101080902"),
    "4504a403": ("锦州", "101070701"),
    "e8ce44a8": ("镇江", "101190301"),
    "675a9579": ("长春", "101060101"),
    "17504a6f": ("长沙", "101250106"),
    "bd24d733": ("长治", "101100598"),
    "044a7b39": ("阜新", "101070901"),
    "c43800d7": ("阜阳", "101220801"),
    "0f827489": ("防城港", "101301401"),
    "77f80edf": ("阳江", "101281801"),
    "21eff129": ("阳泉", "101100301"),
    "7d41557a": ("阿克苏", "101130801"),
    "6273efc3": ("阿勒泰", "101131401"),
    "2bcfbb0f": ("阿坝州", "101271901"),
    "fea339bb": ("阿拉善盟", "101081213"),
    "99dcb6cb": ("阿里", "101140701"),
    "4d8bf1b0": ("陇南", "101161010"),
    "9bc80915": ("陵水", "101310216"),
    "6e1dc57f": ("随州", "101201301"),
    "67548119": ("雅安", "101271701"),
    "1be7eb4d": ("霍邱县", "101091010"),
    "eb447571": ("青岛", "101120201"),
    "24a579e4": ("鞍山", "101070301"),
    "5cfe35d8": ("韶关", "101280201"),
    "064e3cde": ("香港", "101320101"),
    "29a34245": ("香港岛", "101320101"),
    "cfe467f0": ("马鞍山", "101220501"),
    "f89b3be9": ("驻马店", "101181601"),
    "07af6bd6": ("高雄", "101340201"),
    "d68d7466": ("高雄市", "101340201"),
    "17f1f199": ("鸡西", "101051101"),
    "696ee755": ("鹤壁", "101181201"),
    "30d8d724": ("鹤岗", "101051201"),
    "f6abac3e": ("鹰潭", "101241101"),
    "d5437e7c": ("黄冈", "101200501"),
    "1f15f60c": ("黄南州", "101150301"),
    "9a5e340e": ("黄山", "101221001"),
    "2b4b5000": ("黄石", "101200601"),
    "38453f80": ("黑河", "101050601"),
    "5f895ed1": ("黔东南州", "101260506"),
    "bf82ee31": ("黔南州", "101260413"),
    "0d4cefe6": ("黔西南州", "101260708"),
    "ecf7771e": ("齐齐哈尔", "101050201"),
    "ddc5d59e": ("龙岩", "101230701"),
}

# 监测站映射（部分示例）
STATION_MAPPING = {
    "bbafa1b1": "阿城会宁",
    "35bafa91": "阿里藏医院",
    "67aae2d8": "阿里监测站",
    "b78f1733": "艾青诗歌馆",
    "9fa31383": "安钢职工学校",
    "d7b3176e": "安吉城东",
    # ... 可从 utils.py 的 air_matters_map('point') 中提取更多
}


def get_db_url():
    """获取数据库连接URL"""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3307")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    db = os.getenv("DB_NAME", "weather")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"


def fetch_aqi_batch(place_ids: list) -> list:
    """批量获取AQI数据"""
    api_key = os.getenv("AIR_MATTERS_KEY", "")
    if not api_key:
        logger.error("❌ 未配置 AIR_MATTERS_KEY，请在 .env 中设置")
        return []

    url = "https://api-cn.air-matters.com/batch"

    # 确保API Key是ASCII编码
    try:
        api_key_ascii = api_key.encode("ascii").decode("ascii")
    except UnicodeEncodeError:
        logger.error("❌ API Key包含非ASCII字符，请检查配置")
        return []

    headers = {"Authorization": api_key_ascii, "Content-Type": "application/json; charset=utf-8"}

    saved_places = [{"place_id": pid} for pid in place_ids]
    body = json.dumps(
        {
            "saved_places": saved_places,
            "user_info": {"lang": "zh-Hans", "preferred_standard": "aqi_cn"},
            "scope": ["place", "latest", "saved_places"],
        },
        ensure_ascii=False,
    )

    try:
        with httpx.Client(timeout=30) as client:
            # 确保请求体是字节类型
            if isinstance(body, str):
                body = body.encode("utf-8")
            logger.debug(f"请求URL: {url}")
            logger.debug(f"请求头: Authorization={api_key_ascii[:10]}...")
            logger.debug(f"请求体长度: {len(body)} 字节")
            resp = client.post(url, headers=headers, content=body)
            logger.debug(f"响应状态码: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            return data.get("saved_places", [])
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        logger.error(f"请求失败: {type(e).__name__}: {str(e)}")
        return []


def parse_aqi_data(item: dict) -> dict:
    """解析单条AQI数据"""
    place_info = item.get("place", {})
    latest_info = item.get("latest", {})
    readings = latest_info.get("readings", [])

    if not readings:
        return None

    result = {
        "place_id": place_info.get("place_id"),
        "place_type": place_info.get("type"),  # city 或 station
        "place_name": place_info.get("name"),
        "city_name": place_info.get("city_name"),
        "update_time": latest_info.get("update_time"),
    }

    # 解析各项污染物数据
    for reading in readings:
        kind = reading.get("kind", "").lower()
        value = reading.get("value")
        if kind and value:
            with contextlib.suppress(ValueError, TypeError):
                result[kind] = float(value)

    return result


def calculate_iaqi(result: dict) -> dict:
    """计算IAQI分指数（简化版）"""
    # 这里简化处理，实际应该使用完整的IAQI计算公式
    # 参考 downloader/aqi/aqi/spiders/utils.py 中的计算逻辑

    # PM2.5 IAQI
    if "pm25" in result and result["pm25"]:
        pm25 = result["pm25"]
        if pm25 <= 35:
            result["pm25_iaqi"] = int(pm25 * 50 / 35)
        elif pm25 <= 75:
            result["pm25_iaqi"] = int(50 + (pm25 - 35) * 50 / 40)
        elif pm25 <= 115:
            result["pm25_iaqi"] = int(100 + (pm25 - 75) * 50 / 40)
        elif pm25 <= 150:
            result["pm25_iaqi"] = int(150 + (pm25 - 115) * 50 / 35)
        elif pm25 <= 250:
            result["pm25_iaqi"] = int(200 + (pm25 - 150) * 100 / 100)
        elif pm25 <= 350:
            result["pm25_iaqi"] = int(300 + (pm25 - 250) * 100 / 100)
        else:
            result["pm25_iaqi"] = int(400 + (pm25 - 350) * 100 / 150)

    # PM10 IAQI
    if "pm10" in result and result["pm10"]:
        pm10 = result["pm10"]
        if pm10 <= 50:
            result["pm10_iaqi"] = int(pm10)
        elif pm10 <= 150:
            result["pm10_iaqi"] = int(50 + (pm10 - 50) * 50 / 100)
        elif pm10 <= 250:
            result["pm10_iaqi"] = int(100 + (pm10 - 150) * 50 / 100)
        elif pm10 <= 350:
            result["pm10_iaqi"] = int(150 + (pm10 - 250) * 50 / 100)
        elif pm10 <= 420:
            result["pm10_iaqi"] = int(200 + (pm10 - 350) * 100 / 70)
        elif pm10 <= 500:
            result["pm10_iaqi"] = int(300 + (pm10 - 420) * 100 / 80)
        else:
            result["pm10_iaqi"] = int(400 + (pm10 - 500) * 100 / 100)

    # AQI取最大值
    iaqi_values = []
    for key in ["pm25_iaqi", "pm10_iaqi", "so2_iaqi", "no2_iaqi", "o3_iaqi", "co_iaqi"]:
        if key in result and result[key]:
            iaqi_values.append(result[key])

    if iaqi_values:
        result["aqi"] = max(iaqi_values)

    return result


def save_city_aqi(session, data: dict):
    """保存城市AQI数据"""
    place_id = data.get("place_id")
    city_info = CITY_MAPPING.get(place_id)

    if not city_info:
        logger.warning(f"未知城市ID: {place_id}")
        return False

    city_name, system_city_id = city_info

    # 计算IAQI
    data = calculate_iaqi(data)

    # 创建记录
    record = AQICity(
        city_id=system_city_id,  # 使用系统的city_id
        city_name=city_name,
        update_time=data.get("update_time"),
        aqi=data.get("aqi"),
        pm25=data.get("pm25"),
        pm25_iaqi=data.get("pm25_iaqi"),
        pm10=data.get("pm10"),
        pm10_iaqi=data.get("pm10_iaqi"),
        so2=data.get("so2"),
        so2_iaqi=data.get("so2_iaqi"),
        no2=data.get("no2"),
        no2_iaqi=data.get("no2_iaqi"),
        o3=data.get("o3"),
        o3_iaqi=data.get("o3_iaqi"),
        co=data.get("co"),
        co_iaqi=data.get("co_iaqi"),
        source="air_matters",
    )

    session.add(record)
    return True


def save_station_aqi(session, data: dict):
    """保存监测站AQI数据"""
    place_id = data.get("place_id")
    station_name = STATION_MAPPING.get(place_id, data.get("place_name", "未知站点"))

    # 计算IAQI
    data = calculate_iaqi(data)

    # 创建记录
    record = AQIStation(
        station_code=place_id,
        station_name=station_name,
        city_id=data.get("city_id"),
        city_name=data.get("city_name"),
        update_time=data.get("update_time"),
        aqi=data.get("aqi"),
        pm25=data.get("pm25"),
        pm25_iaqi=data.get("pm25_iaqi"),
        pm10=data.get("pm10"),
        pm10_iaqi=data.get("pm10_iaqi"),
        so2=data.get("so2"),
        so2_iaqi=data.get("so2_iaqi"),
        no2=data.get("no2"),
        no2_iaqi=data.get("no2_iaqi"),
        o3=data.get("o3"),
        o3_iaqi=data.get("o3_iaqi"),
        co=data.get("co"),
        co_iaqi=data.get("co_iaqi"),
        source="air_matters",
    )

    session.add(record)
    return True


def download_all():
    """下载所有城市AQI数据"""
    logger.info("开始下载AQI数据...")

    # 获取所有城市ID
    city_ids = list(CITY_MAPPING.keys())
    logger.info(f"准备下载 {len(city_ids)} 个城市的数据")

    # 分批下载（每批最多100个）
    batch_size = 100
    all_data = []

    for i in range(0, len(city_ids), batch_size):
        batch_ids = city_ids[i : i + batch_size]
        logger.info(f"下载批次 {i // batch_size + 1}: {len(batch_ids)} 个城市")

        batch_data = fetch_aqi_batch(batch_ids)
        all_data.extend(batch_data)

        # 避免请求过于频繁
        if i + batch_size < len(city_ids):
            time.sleep(1)

    logger.info(f"获取到 {len(all_data)} 条数据")

    # 连接数据库
    engine = get_engine(url=get_db_url())
    create_tables(engine)
    session = get_session(engine)

    try:
        city_count = 0
        station_count = 0

        for item in all_data:
            data = parse_aqi_data(item)
            if not data:
                continue

            if data.get("place_type") == "station":
                if save_station_aqi(session, data):
                    station_count += 1
            else:
                if save_city_aqi(session, data):
                    city_count += 1

        session.commit()
        logger.info(f"✅ 下载完成: 城市 {city_count} 条, 监测站 {station_count} 条")

    except Exception as e:
        session.rollback()
        logger.error(f"❌ 保存失败: {e}")
    finally:
        session.close()


def download_city(city_name: str):
    """下载指定城市AQI数据"""
    # 查找城市ID
    city_id = None
    for pid, (name, _) in CITY_MAPPING.items():
        if name == city_name:
            city_id = pid
            break

    if not city_id:
        logger.error(f"未找到城市: {city_name}")
        logger.info(f"支持的城市: {', '.join({name for name, _ in CITY_MAPPING.values()})}")
        return

    logger.info(f"Downloading AQI data for {city_name}...")

    # 下载数据
    data_list = fetch_aqi_batch([city_id])

    if not data_list:
        logger.warning("未获取到数据")
        return

    # 连接数据库
    engine = get_engine(url=get_db_url())
    create_tables(engine)
    session = get_session(engine)

    try:
        for item in data_list:
            data = parse_aqi_data(item)
            if not data:
                continue

            if data.get("place_type") == "station":
                if save_station_aqi(session, data):
                    logger.info(f"保存监测站数据: {data.get('place_name')}")
            else:
                if save_city_aqi(session, data):
                    logger.info(f"保存城市数据: {city_name}")

        session.commit()
        logger.info("✅ 下载完成")

    except Exception as e:
        session.rollback()
        logger.error(f"❌ 保存失败: {e}")
    finally:
        session.close()


def list_cities():
    """列出支持的城市"""
    print("支持的城市列表:")
    print("=" * 50)

    cities = set()
    for city_id, (name, system_id) in CITY_MAPPING.items():
        cities.add((name, city_id, system_id))

    for name, city_id, system_id in sorted(cities):
        print(f"{name:10} | {city_id:10} | {system_id}")


def get_aqi_level(aqi: int) -> str:
    """获取AQI等级

    Args:
        aqi: AQI指数

    Returns:
        str: AQI等级
    """
    if aqi is None:
        return None

    if aqi <= 50:
        return "优"
    if aqi <= 100:
        return "良"
    if aqi <= 150:
        return "轻度污染"
    if aqi <= 200:
        return "中度污染"
    if aqi <= 300:
        return "重度污染"
    return "严重污染"


def get_aqi_description(level: str) -> str:
    """获取AQI等级描述

    Args:
        level: AQI等级

    Returns:
        str: 等级描述
    """
    descriptions = {
        "优": "空气质量令人满意，基本无空气污染",
        "良": "空气质量可接受，某些污染物可能对少数人健康有轻微影响",
        "轻度污染": "敏感人群症状有轻度加剧，健康人群出现刺激症状",
        "中度污染": "进一步加剧敏感人群症状，可能对心脏和呼吸系统有影响",
        "重度污染": "健康人群运动耐受力降低，有明显强烈症状",
        "严重污染": "健康人群运动耐受力降低，有明显强烈症状，提前采取措施",
    }
    return descriptions.get(level, "")


def get_health_advice(level: str) -> dict:
    """获取健康建议

    Args:
        level: AQI等级

    Returns:
        dict: 健康建议
    """
    advice = {
        "优": {
            "general": "适宜户外活动",
            "sensitive": "可正常进行户外活动",
            "outdoor": "适宜",
            "mask": "不需要",
        },
        "良": {
            "general": "可正常户外活动",
            "sensitive": "减少长时间、高强度的户外活动",
            "outdoor": "适宜",
            "mask": "不需要",
        },
        "轻度污染": {
            "general": "减少户外活动",
            "sensitive": "避免户外活动，外出时佩戴防护口罩",
            "outdoor": "减少",
            "mask": "敏感人群需要",
        },
        "中度污染": {
            "general": "减少户外活动，外出时佩戴防护口罩",
            "sensitive": "避免户外活动，尽量留在室内",
            "outdoor": "减少",
            "mask": "需要",
        },
        "重度污染": {
            "general": "避免户外活动，外出时佩戴防护口罩",
            "sensitive": "留在室内，关闭门窗",
            "outdoor": "避免",
            "mask": "必须佩戴",
        },
        "严重污染": {
            "general": "留在室内，关闭门窗",
            "sensitive": "留在室内，开启空气净化器",
            "outdoor": "禁止",
            "mask": "必须佩戴",
        },
    }
    return advice.get(level, {})


def main():
    parser = argparse.ArgumentParser(description="AQI数据下载器")
    parser.add_argument("--city", type=str, help="下载指定城市AQI数据")
    parser.add_argument("--list", action="store_true", help="列出支持的城市")

    args = parser.parse_args()

    if args.list:
        list_cities()
    elif args.city:
        download_city(args.city)
    else:
        download_all()


if __name__ == "__main__":
    main()
