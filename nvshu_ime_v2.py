"""
女书输入法 v2 - Nüshu IME (模拟真实输入法体验)
- 低层键盘钩子: 拦截任意窗口/输入框的按键
- Ctrl+N+S: 切换女书输入模式
- 细长候选条: 仅显示女书字方块，按优先级排序
- SendInput: 直接输出 Unicode 女书字，无剪贴板依赖
"""

import os
import sys
import time
import threading
import ctypes
import urllib.request
from ctypes import wintypes, CFUNCTYPE, POINTER, Structure, c_ulong, c_int
from pathlib import Path

# --- PyQt6 ---
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QSystemTrayIcon, QMenu, QFrame, QGraphicsDropShadowEffect, QDialog,
    QTextEdit, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QFont, QAction, QFontDatabase,
    QClipboard,
)

# --- 拼音库 ---
try:
    from pypinyin import pinyin as to_pinyin, Style
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False

# ============================================================
# 女书数据 (与之前相同)
# ============================================================
NUSHU_RAW = [
    ("i5", "𛅰", "一"), ("na33", "𛅱", "两日入二"), ("tsha5", "𛅲", "傺错七"),
    ("ie21", "𛅳", "人"), ("poe5", "𛅴", "八"), ("swe33", "𛅵", "十事实侍拾莳是誓"),
    ("phiu44", "𛅶", "标蜂漂飘批披喷片骗"), ("u5", "𛅷", "约雨宇羽舞屋武"),
    ("cya35", "𛅸", "水"), ("tie42", "𛅹", "了礼弟帝吊调丫"),
    ("njie33", "𛅺", "内义要语宜仪谊议意遗蚁以认忍耳"), ("toe33", "𛅻", "大代袋待怠台抬"),
    ("tchye5", "𛅼", "尺嘱烛却"), ("fwe13", "𛅽", "下吓化"), ("liu44", "𛅾", "朝犁低刁雕"),
    ("siu35", "𛅿", "小细笑洗息夕削叔送宋宿"), ("thu35", "𛆀", "土"),
    ("njyu13", "𛆁", "女"), ("vai42", "𛆂", "文闻"),
    ("kai44", "𛆃", "坑间工公跟竿功更根庚耕"), ("khau21", "𛆄", "寸可靠壳扩考介戒界狗苟稿确吧"),
    ("kou21", "𛆅", "界介顾个告够过"), ("tciou35", "𛆆", "者九久韭酒守"),
    ("liang35", "𛆇", "两二"), ("ciang13", "𛆈", "向上食"), ("tsheng44", "𛆉", "干千签迁"),
    ("song44", "𛆊", "三"), ("ma5", "𛆋", "没"), ("fa44", "𛆌", "辉挥坏灰非飞饭翻番反费虽"),
    ("la44", "𛆍", "知泪虑立利粒单丹"), ("thoe21", "𛆎", "太"), ("tsoe42", "𛆏", "才财裁"),
    ("fwe44", "𛆐", "虾括骨刮发"), ("tswe35", "𛆑", "此翅池子只纸指旨紫趾仔崽"),
    ("ti13", "𛆒", "称曾了拉弄弟刀动低洞第得灯登滴冻凳待带铜腾替驼潭"),
    ("ci21", "𛆓", "戏习世势逝"), ("fu44", "𛆔", "夫傅"), ("fu35", "𛆕", "补火幅府妇"),
    ("fu13", "𛆖", "贺祸户互父妇负富腐咐付赋附福服伏"), ("tcyu35", "𛆗", "主煮矩举"),
    ("tcyu21", "𛆘", "嘴句"), ("fai44", "𛆙", "扮婚昏魂患纷分封坟份粉粪风睡"),
    ("hau35", "𛆚", "口考肯好候"), ("lou35", "𛆛", "斗抖到"), ("liou33", "𛆜", "六略"),
    ("tciou44", "𛆝", "筹抽昼州周洲咒交旧娇绞教救较究舅纠求球丘"),
    ("ciou35", "𛆞", "丑手首守"), ("tchyn21", "𛆟", "串劝"),
    ("fang44", "𛆠", "方芳风封丰妨逢凤番翻"), ("vang42", "𛆡", "亡忘"),
    ("sang33", "𛆢", "葬算丧蒜"), ("khang21", "𛆣", "看炕靠叩扣孔勘砍扛杠贯杆干"),
    ("theng44", "𛆤", "天汤通贪"), ("neng44", "𛆥", "年侬然燃"),
    ("piong13", "𛆦", "并兵变豹朝井平瓶拼聘桥茄其奇棋"),
    ("iong42", "𛆧", "赢园元圆源缘原员援院愿荣王完玩"), ("va33", "𛆨", "味位未谓为万湾弯威卫"),
    ("khua44", "𛆩", "亏垮屈"), ("tchya33", "𛆪", "吹"), ("nie33", "𛆫", "内嫩"),
    ("lie21", "𛆬", "处对兑队堆顿凳"), ("tcie44", "𛆭", "真针珍贞斟征金今襟斤巾筋惊徽沈"),
    ("tchie44", "𛆮", "称"), ("njie44", "𛆯", "个夜亦要"), ("njie42", "𛆰", "泥银吟"),
    ("ie44", "𛆱", "吃系音阴因姻殷忆与裕依医衣要以已孕荫于妖腰语药叶易应遗喻瑜幼意任如儒污的了"),
    ("ie33", "𛆲", "吃任"), ("mwe13", "𛆳", "不未"), ("vwe33", "𛆴", "会丫约要曰"),
    ("vwe5", "𛆵", "划压鸭"), ("twe33", "𛆶", "他曲"), ("tswe44", "𛆷", "之滋支"),
    ("swe42", "𛆸", "匙时"), ("swe13", "𛆹", "赐士是氏仕十事实侍师诗尸狮视市示史"),
    ("tci35", "𛆺", "主爪己几纪举缴"), ("ci35", "𛆻", "彻喜枕种肿紧锦少起砌"),
    ("i5", "𛆼", "一以叶"), ("liu44", "𛆽", "猪绿料旅驴"), ("njiu33", "𛆾", "尿"),
    ("ciu35", "𛆿", "少稍"), ("mu13", "𛇀", "母马木目墓麦磨麻亩牡"),
    ("yu44", "𛇁", "拿夜又也右佑亦忧要匀若"), ("tchy21", "𛇂", "翠去趣欺取娶区"),
    ("njy33", "𛇃", "月遇外"), ("y42", "𛇄", "余移欲愚与入如"),
    ("pai35", "𛇅", "本表"), ("pai35", "𛇆", "惭正帐政转整诊拯镜敬竟卷眷京惊渐颈景井警"),
    ("lai42", "𛇇", "怜林淋麟劳僚"), ("ai42", "𛇈", "日入儿而尔恩"),
    ("hau35", "𛇉", "口肯好搞"), ("tou42", "𛇊", "脑投头套"),
    ("liou42", "𛇋", "柳流留刘榴溜"), ("iou13", "𛇌", "后後"),
    ("tsew35", "𛇍", "作左"), ("tsew21", "𛇎", "坐做作综"),
    ("suow44", "𛇏", "生山甥牲笙衫梭馊腮"), ("huow42", "𛇐", "行闲相杏限幸还衡烦"),
    ("huow35", "𛇑", "反"), ("nguw33", "𛇒", "外稳"),
    ("mang42", "𛇓", "眉忙茫蒙盲瞒迷眯蛮"), ("thang44", "𛇔", "汤"),
    ("kang44", "𛇕", "间减烘光官刚功肝冠钢干冈甘棺岗缸柑观公关馆赶敢管感广杆"),
    ("liang33", "𛇖", "亮谅量"), ("tciang35", "𛇗", "长撑掌讲"),
    ("njiang42", "𛇘", "娘"), ("peng44", "𛇙", "便边鞭辫片偏"),
    ("seng44", "𛇚", "先仙鲜"), ("piong42", "𛇛", "丙评平瓶"),
    ("tshiong21", "𛇜", "听"), ("tcing21", "𛇝", "占见建敬件"),
    ("pa5", "𛇞", "笔"), ("la33", "𛇟", "知立泪虑厉利笠雷"),
    ("sie35", "𛇠", "此齿刺次写些伞省且"), ("tcie35", "𛇡", "毑"),
    ("ie21", "𛇢", "个派"), ("poe21", "𛇣", "报被拜摆跛败拔沸皮"),
    ("loe42", "𛇤", "来"), ("tsoe13", "𛇥", "在再载债灾栽"),
    ("soe5", "𛇦", "采插踩煞杀刹死"), ("koe44", "𛇧", "揩街阶皆架价嫁介乖该改盖告怪"),
    ("khuoe21", "𛇨", "快块"), ("ye21", "𛇩", "忧夜运野益闰惹弱"),
    ("pwe33", "𛇪", "把白吧便变拍培"), ("pwe5", "𛇫", "百佰柏北拔拨钵迫拍泼"),
    ("tchi21", "𛇬", "既气弃契"), ("tsiu33", "𛇭", "除厨住柱助足聚樵"),
    ("fu42", "𛇮", "鞋和何蝴荷胡豪毫耗芙扶吗呢"), ("vu42", "𛇯", "嬷禾和雨鹅无武乌"),
    ("khu35", "𛇰", "苦枯虎湖古果鼓股故过固"), ("hu5", "𛇱", "哭屋"),
    ("pw13", "𛇲", "拨背杯变卜霸妇陪拍怕帕配赔聘"), ("fw42", "𛇳", "华回费"),
    ("sw5", "𛇴", "曾侄色塞是始使适宿"), ("kw5", "𛇵", "滑葛割物"),
    ("hw44", "𛇶", "开孩害"), ("mai42", "𛇷", "门民毛眉闻"),
    ("thai44", "𛇸", "吞"), ("sai44", "𛇹", "辛心新森"), ("sai44", "𛇺", "悯心新"),
    ("thau35", "𛇻", "讨"), ("lau21", "𛇼", "老到倒斗道稻凳汪"),
    ("lau21", "𛇽", "老到凳"), ("nou33", "𛇾", "明名鸣哪抛"),
    ("kou33", "𛇿", "阁搁罐"), ("ciou44", "𛈀", "休收岸"),
    ("lew44", "𛈁", "落洛丹多单"), ("sew35", "𛈂", "吵所锁"),
    ("thuow21", "𛈃", "炭"), ("uow33", "𛈄", "万湾弯"),
    ("kuw5", "𛈅", "甲嘉价国隔格寡股果滚"), ("tcyn42", "𛈆", "传程呈缠全权泉乾拳"),
    ("yn35", "𛈇", "映院苑影"), ("vang33", "𛈈", "忘望枉妄汪"),
    ("tsang44", "𛈉", "床藏庄妆装宗桩状撞浅"), ("sang44", "𛈊", "栅双霜桑酸丧"),
    ("khang35", "𛈋", "孔"), ("tciang44", "𛈌", "中章终张忠专涨樟江姜疆恭宫刚钢公共供弓"),
    ("iang13", "𛈍", "用养样央让"), ("teng42", "𛈎", "垫田"),
    ("neng33", "𛈏", "念闹怒哪内侬炼练联验砚艳研"), ("piong33", "𛈐", "病兵篇拼"),
    ("miong33", "𛈑", "命"), ("ciong42", "𛈒", "成城诚船悬凡盛"),
    ("ciong21", "𛈓", "圣"), ("njing42", "𛈔", "言然"),
    ("ng13", "𛈕", "暗案邀颜岩硬五碗我位"), ("tsa35", "𛈖", "早姊走澡盏者"),
    ("sa21", "𛈗", "四散晒瘦扫"), ("kua44", "𛈘", "归规龟关"),
    ("kua35", "𛈙", "鬼癸诡"), ("cya5", "𛈚", "出"),
    ("cie44", "𛈛", "兴申身深升伸剩"), ("phoe35", "𛈜", "派"),
    ("foe42", "𛈝", "怀"), ("loe35", "𛈞", "辣俫"), ("tshoe44", "𛈟", "猜差"),
    ("tshoe21", "𛈠", "菜蔡"), ("oe44", "𛈡", "衣啊"), ("tchye35", "𛈢", "扯蠢托拖牵"),
    ("fwe44", "𛈣", "虾夏花话灰悔画"), ("tswe33", "𛈤", "自字之枝脂姿滋兹支只贼制则寺"),
    ("ni33", "𛈥", "逆孽泥业热"), ("tshi5", "𛈦", "切"), ("tshi5", "𛈧", "妾"),
    ("si44", "𛈨", "西犀消肖宵逍毫妻凄"), ("fu33", "𛈩", "合喝服伏付赴务"),
    ("ngu13", "𛈻", "我瓦"), ("tchyu21", "𛈫", "处"), ("cyu44", "𛈬", "书输舒树赎粟"),
    ("phw21", "𛈭", "譬佩迫配"), ("fai42", "𛈮", "魂坟"),
    ("tsai13", "𛈯", "长重皂尽进祭讲"), ("lou42", "𛈰", "牛楼劳"),
    ("tsou5", "𛈱", "座浊昨作"), ("piou44", "𛈲", "包胞剥饱抛"),
    ("miou13", "𛈳", "茅卯苗酉"), ("tchiou21", "𛈴", "臭"),
    ("njiou33", "𛈵", "肉"), ("iou13", "𛈶", "酉有友幼与"),
    ("nuow42", "𛈷", "难能"), ("kuow44", "𛈸", "间更耕"),
    ("huow21", "𛈹", "喊"), ("pang44", "𛈺", "半般帮搬伴啄饭放判胖"),
    ("ang21", "𛈪", "你恼"), ("tsiang44", "𛈼", "像相纵丈将浆蒋匠"),
    ("tsiang42", "𛈽", "长从详祥墙"), ("ciang42", "𛈾", "暖常尝偿雄熊裳"),
    ("iang42", "𛈿", "阳羊杨扬洋容蓉绒融"), ("liong42", "𛉀", "宁灵零龄论"),
    ("tshiong35", "𛉁", "请"), ("ciong44", "𛉂", "兄声"),
    ("cing35", "𛉃", "显险掀现扇"), ("la13", "𛉄", "里理鲤李履懒裹旦"),
    ("cya42", "𛉅", "垂婿卷谁诉数睡述随虽"), ("poe42", "𛉆", "排匹"),
    ("thoe44", "𛉇", "胎"), ("noe33", "𛉈", "哪奈耐挪"),
    ("tshoe44", "𛉉", "钗差缠卷捐乾"), ("kue44", "𛉊", "宅助家加佳瓜"),
    ("kue35", "𛉨", "假价驾寡"), ("kue21", "𛉌", "揩嫁架价街皆阶挂怪卦乖"),
    ("ye42", "𛉍", "爹云爷匀乌污"), ("pwe35", "𛉎", "比彼把宝保板壁被婢摆榜扳"),
    ("vwe35", "𛉏", "哑"), ("thi5", "𛉐", "铁踢贴"),
    ("tsi42", "𛉑", "层蚕采赠斋尽进调齐樵"), ("tsi42", "𛉒", "残惨祭娇济秦齐"),
    ("tci21", "𛉓", "绪制照兆赵站植占注计记季寄跽继既叫及忌纪桂直"),
    ("tci21", "𛉔", "照赵种记寄"), ("tshiu21", "𛉕", "跳剃替"),
    ("pu33", "𛉖", "步薄抱部玻晡布博补夫腹甫婆蒲破铺扑"),
    ("tsu42", "𛉗", "茶查锄搽"), ("ku21", "𛉘", "逼辣癞赖更顾告过故盖的推"),
    ("tcyu44", "𛉙", "珠朱拄具"), ("njyu33", "𛉚", "玉欲窝往"),
    ("tchy35", "𛉛", "处娶取岂启"), ("pw5", "𛉜", "北拔"),
    ("hw35", "𛉝", "扯海害笋舍损耍舜捨"), ("phai35", "𛉞", "品"),
    ("mai33", "𛉟", "慢孟米莫麦每蜜眯庙妙买谋与问"), ("lai35", "𛉠", "等"),
    ("sai21", "𛉡", "信讯送宋"), ("hai42", "𛉢", "红洪鸿"),
    ("mau33", "𛉣", "冒帽"), ("tshau35", "𛉤", "草吵炒楚套"),
    ("hau33", "𛉥", "号"), ("kou5", "𛉦", "喝个各阁搁恶"),
    ("ou44", "𛉧", "欧"), ("tsiou33", "𛉋", "绸袖总坤就共"),
    ("tshiou44", "𛉩", "畜秋"), ("siou44", "𛉪", "羞修"),
    ("tciou5", "𛉫", "粥祝角觉"), ("ciou13", "𛉬", "仇酬效校孝学寿受授熟"),
    ("thuow44", "𛉭", "通滩"), ("fang13", "𛉮", "奉放"),
    ("vang5", "𛉯", "窝亡枉"), ("lang44", "𛉰", "当端"),
    ("tshang44", "𛉱", "聪窗餐仓苍葬枪迁腔抢"), ("khang44", "𛉲", "空康宽堪"),
    ("khang5", "𛉳", "砍"), ("liang42", "𛉴", "良粮龙凉梁粱隆亮量"),
    ("siang44", "𛉵", "凑相箱镶湘厢松"), ("ciang44", "𛉶", "香乡胸伤商尚"),
    ("ciang35", "𛉷", "响享"), ("neng35", "𛉸", "念点典"),
    ("leng42", "𛉹", "线连莲"), ("nong42", "𛉺", "男南"),
    ("long35", "𛉻", "胆但担坦"), ("liong13", "𛉼", "宁冷岭领另令灵龄零丁钉"),
    ("tsiong13", "𛉽", "静净精睛定"), ("siong44", "𛉾", "参星姓性簪"),
    ("tcing44", "𛉿", "占经坚兼肩"), ("tcing44", "𛊀", "缠展沾捡"),
    ("cing42", "𛊁", "贤嫌形刑"), ("ing21", "𛊂", "你燕咽"),
    ("ng44", "𛊃", "磨安鞍庵嗯饿碗误"), ("va42", "𛊄", "为唯围微违维伪"),
    ("sa35", "𛊅", "坐做作死"), ("lie42", "𛊆", "雷"), ("tshie21", "𛊇", "退"),
    ("sie5", "𛊈", "昔惜锡积绩借"), ("ie13", "𛊉", "吃引应任我"),
    ("moe13", "𛊊", "买嬷埋奶尾萎"), ("loe21", "𛊋", "捉带"),
    ("tchye44", "𛊌", "春村车撑"), ("cye44", "𛊍", "靴逊训孙石顺射社舍赦笋停"),
    ("pi33", "𛊎", "别离厘篱璃罗"), ("ti44", "𛊏", "梯"),
    ("tci5", "𛊐", "吸职折织执酌汁吉结急级击劫洁脚菊决"), ("tsiu44", "𛊑", "皱焦蕉椒"),
    ("pu5", "𛊒", "腹斧"), ("fu21", "𛊓", "祸妇富附负"),
    ("thu35", "𛊔", "土塔"), ("hu42", "𛊕", "匣河喊"),
    ("tcy13", "𛊖", "著着惧借菌祀"), ("cy5", "𛊗", "雪血歇硕设识室"),
    ("pw42", "𛊘", "逢浮朋陪贫蓬盆袍赔"), ("khw5", "𛊙", "刻"),
    ("lai44", "𛊚", "弄东灯登冬低"), ("sai44", "𛊛", "辛心新"),
    ("sau35", "𛊜", "产减省嫂伞"),
    ("tsou42", "𛊝", "愁沉尘陈撑曹遭至志智制治种证镇禁髻似穷勤琴芹"),
    ("ngou42", "𛊞", "牛"), ("tsiou33", "𛊟", "酒"),
    ("njiou13", "𛊠", "咬"), ("ciou5", "𛊡", "法叔"),
    ("iou42", "𛊢", "鱼由游油犹尤衙牙芽渔柔娥鹅吴"), ("yn44", "𛊣", "英"),
    ("tang42", "𛊤", "迟地赏同堂团塘童棠唐谈桃萄逃统"),
    ("lang42", "𛊥", "郎狼朗短党挡当端断栋"), ("kang35", "𛊦", "广管敢感赶馆"),
    ("hang44", "𛊧", "糠欢荒汉换焕汗唤旱翰"),
    ("hang42", "𛊨", "行衔咸黄寒皇杭含韩烦"), ("siang35", "𛊩", "想响相恐抢"),
    ("tciang13", "𛊪", "层长像象重丈仗种帐众奏皱灶皂造降颂"),
    ("iang44", "𛊫", "鸳鸯秧英婴烟染"), ("meng42", "𛊬", "梅眠媒棉绵枚"),
    ("tsiong42", "𛊭", "停廷亭庭厅清情晴青"), ("siong21", "𛊮", "姓性幸犯岁鸭"),
    ("tchiong44", "𛊯", "穿川轻卿倾"), ("pa33", "𛊰", "悲碑被婢备避拔辈斑贝"),
    ("tshie5", "𛊱", "脱"), ("sie5", "𛊲", "昔惜肯恨憾"),
    ("tsoe44", "𛊳", "灾斋"), ("koe35", "𛊴", "解矮且"),
    ("tcye44", "𛊵", "尊遵诸遮军君均居闺裙"),
    ("tcye42", "𛊶", "存巡膝袖竹罪最蔗尊炙转跨裤俊军郡裙"),
    ("pwe35", "𛊷", "把"), ("swe44", "𛊸", "屎思司丝师诗私狮尸施斯恩"),
    ("ti42", "𛊹", "啼提"), ("i42", "𛊺", "移姨摇窑油游依"),
    ("tciu42", "𛊻", "朝场肠长重渐其墙桥茄乔骑奇旗期棋麒祁强"),
    ("ciu44", "𛊼", "痴稀希食烧岁失属输淑欺"), ("tsu35", "𛊽", "祖组阻赌"),
    ("tshu35", "𛊾", "骂初粗差操须租宅助梳疏纱沙杉苏蓑蔬"),
    ("ku44", "𛊿", "孤姑锅估改"), ("lw5", "𛋀", "德得答"),
    ("mai42", "𛋁", "门闻"), ("kau44", "𛋂", "篮高糕篙哥孤勾钩沟稿敲"),
    ("thou21", "𛋃", "兜透痛探偷贪滔"), ("hou33", "𛋄", "候喊"),
    ("pang42", "𛋅", "螃环房妨逢防纺访盘旁亡玩"),
    ("fang44", "𛋆", "宾冰掰风妨封分份凭问"), ("tang13", "𛋇", "断地段缎短端"),
    ("lang33", "𛋈", "浪乱短党端断"), ("meng33", "𛋉", "墨妹面免敏梅枚"),
    ("teng42", "𛋊", "殿电垫佃田恬填甜"), ("tseng42", "𛋋", "贱尖箭严然前钱浅泉"),
    ("cing13", "𛋌", "现善扇"), ("ing42", "𛋍", "默蔫盈阎盐炎严赢郁抑迎忧延仍"),
    ("tsa33", "𛋎", "浸"), ("tsie21", "𛋏", "借"), ("cie21", "𛋐", "兴虚胜甚剩"),
    ("moe42", "𛋑", "埋"), ("li35", "𛋒", "鸟煮底抵越体桶主"),
    ("tsi5", "𛋓", "猫茅苗拆策直指摘责节接借截实"),
    ("tci44", "𛋔", "朝嬉招直值置蛰这娇鸡饥机基稽轿急及极忌寂居俱绝襟金闺麒"),
    ("i35", "𛋕", "倚椅依扰"), ("mu33", "𛋖", "莫"),
    ("lu21", "𛋗", "路露禄腊芦炉卢庐鲁鸬掳妒都"), ("hu42", "𛋘", "湖河胡壶"),
    ("cyu33", "𛋙", "辰承乘晨神树赎深丞绍殊竖"), ("hw5", "𛋚", "黑害"),
    ("tau13", "𛋛", "道稻豆"), ("siou21", "𛋜", "绣秀"),
    ("lew33", "𛋝", "落洛"), ("tshew5", "𛋞", "错"),
    ("yn13", "𛋟", "县远冤渊愿怨往"), ("tong13", "𛋠", "淡潭"),
    ("ie35", "𛋡", "吃饮隐"), ("voe5", "𛋢", "挖"),
    ("tswe21", "𛋣", "慈辞池持迟"), ("i21", "𛋤", "既意以已"),
    ("tu33", "𛋥", "舂独毒达度渡窦肚读薯榻踏屠图"), ("lu35", "𛋦", "堵赌"),
    ("lou33", "𛋧", "乐漏兜蔸"), ("tsou42", "𛋨", "爱"),
    ("tsuow44", "𛋩", "争"), ("mang13", "𛋪", "美满梦摸摩蒙判胖网"),
    ("tciang33", "𛋫", "总困贵挂怪跪更棍桂拐"), ("tchiang21", "𛋬", "唱铳仗"),
    ("tciong44", "𛋭", "正惊京荆精兢"), ("tsie33", "𛋮", "谢席夕阵借笛碟敌"),
    ("moe33", "𛋯", "卖袜"), ("ku44", "𛋰", "科考歌哥孤姑戈"),
    ("cyu35", "𛋱", "许主暑鼠"), ("pw21", "𛋲", "背"),
    ("tsiang42", "𛋳", "沉从长层蚕辞曹巢陈曾昨遭僧"),
    ("tshai44", "𛋴", "葱踩抄操推妻亲侵凄"), ("nguow13", "𛋵", "眼"),
    ("nong44", "𛋶", "会活或话画悔患给佛罚范"), ("fu5", "𛋷", "博忽福复幅腹斧魄"),
    ("ku5", "𛋸", "谷穀鸽歌"), ("fang33", "𛋹", "凤"),
    ("tcye21", "𛋺", "转渐眷"), ("fi21", "𛋻", "费"),
]

INPUT_MODE_NUSHU = "nushu"
INPUT_MODE_PINYIN = "pinyin"

# 常用汉字（按使用频率排序，越靠前越常用）
COMMON_HANZI = "的一是不了人我在有他这为之大来以个中上们到说时地也子就道会那要下看天与多小然自心手前意所行力明本公从重理用并进定方多开始当经动现法加些已两实面起正情已最样又分把种三等外能些着常对开而位工作你行文使知长将望已回见被产教老由常好明因与什表次门常但此已象形"

def _hanzi_priority(hanzi):
    """计算汉字常用度分数，越常用分数越高"""
    if not hanzi:
        return 0
    first = hanzi[0]
    idx = COMMON_HANZI.find(first)
    if idx >= 0:
        return 1000 - idx  # 越靠前分数越高
    return 0

PINYIN_TO_READING = {
    "b": "p", "p": "ph", "d": "t", "t": "th",
    "g": "k", "k": "kh", "z": "ts", "c": "tsh",
    "j": "tc", "q": "tch", "x": "c",
    "nj": "nj", "ng": "ng", "s": "s", "f": "f",
    "v": "v", "m": "m", "n": "n", "l": "l", "h": "h",
}

# ============================================================
# 数据引擎
# ============================================================
class NushuData:
    def __init__(self):
        self.chars = []
        seen = set()
        for r, c, h in NUSHU_RAW:
            k = (c, r)
            if k in seen: continue
            seen.add(k)
            base = ''.join(ch for ch in r if not ch.isdigit())
            self.chars.append({'char': c, 'hanzi': h, 'reading': r, 'base': base})

    def search(self, text):
        if not text: return []
        text = text.lower().strip()
        converted = self._convert(text)
        matches = []
        for ch in self.chars:
            s = 0
            if ch['base'] == text: s = 100
            elif ch['base'].startswith(text): s = 80
            elif converted and ch['base'] == converted: s = 90
            elif converted and ch['base'].startswith(converted): s = 70
            elif text in ch['base']: s = 50
            if s > 0: matches.append({**ch, 'score': s + _hanzi_priority(ch['hanzi']) * 0.01})
        matches.sort(key=lambda x: (-x['score'], x['reading']))
        seen_c = set(); uniq = []
        for m in matches:
            if m['char'] not in seen_c: seen_c.add(m['char']); uniq.append(m)
        return uniq  # 返回所有匹配，由候选条分页显示

    def _convert(self, text):
        for u, d in sorted(PINYIN_TO_READING.items(), key=lambda x: -len(x[0])):
            if text.startswith(u) and len(u) > 1: return d + text[len(u):]
        for u, d in sorted(PINYIN_TO_READING.items(), key=lambda x: -len(x[0])):
            if text.startswith(u): return d + text[len(u):]
        return None


class PinyinData:
    def __init__(self):
        self.map = {}
        seen = set()
        for r, nc, hs in NUSHU_RAW:
            for ch in hs:
                k = (nc, ch)
                if k in seen: continue
                seen.add(k)
                py = self._get_py(ch)
                if py:
                    if py not in self.map: self.map[py] = []
                    self.map[py].append({'char': nc, 'hanzi': ch, 'pinyin': py, 'reading': r})
        print(f"拼音索引: {len(self.map)} 音节, {sum(len(v) for v in self.map.values())} 字")

    def _get_py(self, ch):
        if HAS_PYPINYIN:
            try:
                r = to_pinyin(ch, style=Style.NORMAL)
                if r and r[0]: return r[0][0].lower().replace('ü', 'v')
            except: pass
        return None

    def search(self, text):
        if not text: return []
        text = text.lower().strip()
        matches = []
        for py, chars in self.map.items():
            s = 0
            if py == text: s = 100
            elif py.startswith(text): s = 80
            elif text in py: s = 50
            if s > 0:
                for c in chars: matches.append({**c, 'score': s + _hanzi_priority(c['hanzi']) * 0.01})
        matches.sort(key=lambda x: (-x['score'], x['pinyin'], x['hanzi']))
        seen_k = set(); uniq = []
        for m in matches:
            k = (m['char'], m['hanzi'])
            if k not in seen_k: seen_k.add(k); uniq.append(m)
        return uniq  # 返回所有匹配，由候选条分页显示


# ============================================================
# 低层键盘钩子 (Windows API)
# ============================================================
class KBDLLHOOKSTRUCT(Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),  # ULONG_PTR
    ]

class KEYBDINPUT(Structure):
    _pack_ = 8
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]

class MOUSEINPUT(Structure):
    _pack_ = 8
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]

class HARDWAREINPUT(Structure):
    _pack_ = 8
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]

class INPUT_UNION(ctypes.Union):
    _pack_ = 8
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT),
    ]

class INPUT_STRUCT(Structure):
    _pack_ = 8
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", INPUT_UNION),
    ]

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_KEYUP = 0x0101
WM_SYSKEYUP = 0x0105
VK_CONTROL = 0x11
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_SHIFT = 0x10
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_BACK = 0x08
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_RETURN = 0x0D
VK_PRIOR = 0x21   # PageUp
VK_NEXT = 0x22    # PageDown
VK_LEFT = 0x25
VK_RIGHT = 0x27
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1

HOOKPROC = CFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

# 全局状态（由 NvshuIME 管理）
_hook_state = {
    'active': False,          # 女书模式是否激活
    'composition': '',        # 当前拼音输入缓冲
    'sending': False,         # 正在输出字符，忽略钩子
    'mode': INPUT_MODE_NUSHU,
    'ime': None,              # NvshuIME 实例引用
}


def _send_unicode(char):
    """用剪贴板+Ctrl+V输出字符（比SendInput有更好的字体回退）"""
    _hook_state['sending'] = True
    try:
        # 保存当前剪贴板
        clipboard = QApplication.clipboard()
        old_text = clipboard.text()
        old_mime = clipboard.mimeData()

        # 设置剪贴板内容
        clipboard.setText(char, QClipboard.Mode.Clipboard)

        # 短暂延迟确保剪贴板已更新
        import time
        time.sleep(0.02)

        # 模拟 Ctrl+V
        inp = INPUT_STRUCT()
        inp.type = INPUT_KEYBOARD

        # Ctrl 按下
        inp.ki.wVk = VK_CONTROL
        inp.ki.dwFlags = 0
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

        # V 按下
        inp.ki.wVk = ord('V')
        inp.ki.dwFlags = 0
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

        # V 释放
        inp.ki.dwFlags = KEYEVENTF_KEYUP
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

        # Ctrl 释放
        inp.ki.wVk = VK_CONTROL
        inp.ki.dwFlags = KEYEVENTF_KEYUP
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

        # 延迟后恢复剪贴板
        def restore():
            time.sleep(0.1)
            clipboard.setText(old_text, QClipboard.Mode.Clipboard)

        threading.Thread(target=restore, daemon=True).start()

    finally:
        _hook_state['sending'] = False


def _is_key_pressed(vk):
    """用 Windows API 可靠检测按键是否物理按下"""
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


def _call_next_hook(nCode, wParam, lParam):
    """安全调用 CallNextHookEx"""
    return ctypes.windll.user32.CallNextHookEx(
        ctypes.c_void_p(0), ctypes.c_int(nCode),
        wintypes.WPARAM(wParam), wintypes.LPARAM(lParam))


def _low_level_keyboard_proc(nCode, wParam, lParam):
    """低层键盘钩子回调
    
    热键: Ctrl+Shift+N (简单可靠，不拦截中间键)
    """
    if nCode < 0 or _hook_state['sending']:
        return _call_next_hook(nCode, wParam, lParam)

    kb = ctypes.cast(lParam, POINTER(KBDLLHOOKSTRUCT)).contents
    ime = _hook_state['ime']

    if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
        vk = kb.vkCode

        # --- Ctrl+Shift+N 热键 ---
        if vk == ord('N') and _is_key_pressed(VK_CONTROL) and _is_key_pressed(VK_SHIFT):
            if ime:
                ime._hotkey_signal.emit()
            return 1  # 吞掉 N

        # --- 女书模式下的按键处理 ---
        if _hook_state['active'] and not _is_key_pressed(VK_CONTROL):
            # 数字键 1-8：选择候选
            if 0x31 <= vk <= 0x38:
                idx = vk - 0x31
                if ime:
                    ime._select_signal.emit(idx)
                return 1

            # 字母键：添加到拼音缓冲
            if 0x41 <= vk <= 0x5A:
                ch = chr(vk).lower()
                _hook_state['composition'] += ch
                if ime:
                    ime._type_signal.emit(_hook_state['composition'])
                return 1

            # Backspace：有拼音时删除，无拼音时放行给应用
            if vk == VK_BACK:
                if _hook_state['composition']:
                    _hook_state['composition'] = _hook_state['composition'][:-1]
                    if ime:
                        ime._type_signal.emit(_hook_state['composition'])
                    return 1
                # 没有拼音缓冲，不拦截，让应用处理删除

            # Escape：取消
            if vk == VK_ESCAPE:
                _hook_state['composition'] = ''
                if ime:
                    ime._cancel_signal.emit()
                return 1

            # Space / Enter：选第一个候选
            if vk in (VK_SPACE, VK_RETURN):
                if ime:
                    ime._select_signal.emit(0)
                return 1

            # PageUp / 左箭头：上一页
            if vk in (VK_PRIOR, VK_LEFT):
                if ime:
                    ime._page_signal.emit(-1)
                return 1

            # PageDown / 右箭头：下一页
            if vk in (VK_NEXT, VK_RIGHT):
                if ime:
                    ime._page_signal.emit(1)
                return 1

    return _call_next_hook(nCode, wParam, lParam)


# ============================================================
# 字体安装对话框
# ============================================================
class FontInstallDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("女书字体安装")
        self.setFixedSize(420, 320)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self._init_ui()
        self._check_font()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 标题
        title = QLabel("女书字体安装")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        # 状态图标+文字
        self._status_label = QLabel("正在检测...")
        self._status_label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(self._status_label)

        # 详细信息
        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setMaximumHeight(140)
        self._detail.setStyleSheet("""
            QTextEdit {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                color: #444;
            }
        """)
        layout.addWidget(self._detail)

        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._install_btn = QPushButton("安装字体")
        self._install_btn.setStyleSheet("""
            QPushButton {
                background: #4285f4; color: white;
                border: none; border-radius: 4px;
                padding: 8px 24px; font-size: 14px;
            }
            QPushButton:hover { background: #3367d6; }
            QPushButton:disabled { background: #ccc; }
        """)
        self._install_btn.clicked.connect(self._do_install)
        btn_layout.addWidget(self._install_btn)

        self._close_btn = QPushButton("关闭")
        self._close_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0; color: #333;
                border: 1px solid #ccc; border-radius: 4px;
                padding: 8px 24px; font-size: 14px;
            }
            QPushButton:hover { background: #e0e0e0; }
        """)
        self._close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self._close_btn)

        layout.addLayout(btn_layout)

    def _check_font(self):
        """检测字体安装状态"""
        font_name = "NotoTraditionalNushu-Regular.ttf"
        sys_font = Path(os.environ.get('WINDIR', 'C:/Windows')) / "Fonts" / font_name
        app_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        local_font = app_dir / "fonts" / font_name

        # 检测注册表
        reg_installed = False
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts", 0, winreg.KEY_READ)
            try:
                val, _ = winreg.QueryValueEx(key, "Noto Traditional Nushu (TrueType)")
                reg_installed = True
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
        except:
            pass

        self._sys_installed = sys_font.exists() and reg_installed
        self._local_exists = local_font.exists()

        info_lines = []
        if self._sys_installed:
            self._status_label.setText("女书字体已安装到系统，无需重复安装")
            self._status_label.setStyleSheet("font-size: 14px; color: #2e7d32;")
            self._install_btn.setEnabled(False)
            info_lines.append(f"系统字体路径: {sys_font}")
            info_lines.append(f"注册表: 已注册")
        elif self._local_exists:
            self._status_label.setText("字体仅存在于本地，未安装到系统")
            self._status_label.setStyleSheet("font-size: 14px; color: #e65100;")
            self._install_btn.setEnabled(True)
            info_lines.append(f"本地字体: {local_font}")
            info_lines.append(f"系统字体: 未安装")
            info_lines.append("")
            info_lines.append("点击「安装字体」将字体安装到系统，")
            info_lines.append("这样所有应用都能正确显示女书字符。")
        else:
            self._status_label.setText("未检测到女书字体，需要下载并安装")
            self._status_label.setStyleSheet("font-size: 14px; color: #c62828;")
            self._install_btn.setEnabled(True)
            info_lines.append("本地字体: 不存在")
            info_lines.append("系统字体: 未安装")
            info_lines.append("")
            info_lines.append("点击「安装字体」下载并安装女书字体。")

        self._detail.setText("\n".join(info_lines))

    def _do_install(self):
        """执行安装"""
        self._install_btn.setEnabled(False)
        self._install_btn.setText("安装中...")
        self._status_label.setText("正在安装...")
        self._status_label.setStyleSheet("font-size: 14px; color: #1565c0;")

        threading.Thread(target=self._install_thread, daemon=True).start()

    def _install_thread(self):
        import shutil
        app_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        font_name = "NotoTraditionalNushu-Regular.ttf"
        local_font = app_dir / "fonts" / font_name
        sys_font = Path(os.environ.get('WINDIR', 'C:/Windows')) / "Fonts" / font_name

        msgs = []

        # 下载
        if not local_font.exists():
            try:
                msgs.append("正在下载字体...")
                self._update_detail_signal(msgs)
                fd = app_dir / "fonts"; fd.mkdir(exist_ok=True)
                urllib.request.urlretrieve(
                    "https://notofonts.github.io/nushu/fonts/NotoTraditionalNushu/unhinted/ttf/NotoTraditionalNushu-Regular.ttf",
                    str(local_font)
                )
                msgs.append(f"下载完成: {local_font.stat().st_size} bytes")
            except Exception as e:
                msgs.append(f"下载失败: {e}")
                self._update_detail_signal(msgs)
                self._update_status_signal("❌ 下载失败", "#c62828")
                self._update_btn_signal("重试", True)
                return

        # 注册到当前会话
        ctypes.windll.gdi32.AddFontResourceW(str(local_font))
        msgs.append("已注册到当前会话")

        # 安装到系统
        if sys_font.exists():
            msgs.append("系统字体已存在，跳过复制")
        else:
            try:
                shutil.copy2(str(local_font), str(sys_font))
                ctypes.windll.gdi32.AddFontResourceW(str(sys_font))
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
                    0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "Noto Traditional Nushu (TrueType)", 0, winreg.REG_SZ, font_name)
                winreg.CloseKey(key)
                msgs.append("已安装到系统字体目录")
                msgs.append("已写入注册表")
            except PermissionError:
                msgs.append("⚠️ 需要管理员权限才能安装到系统")
                msgs.append("当前会话已可用，重启后需重新注册")

        # 通知系统
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x001D, 0, 0)
        msgs.append("已通知系统字体变更")

        self._update_detail_signal(msgs)
        self._update_status_signal("✅ 安装完成！", "#2e7d32")
        self._update_btn_signal("已完成", False)

    # 用 QTimer 在主线程更新 UI
    def _update_detail_signal(self, msgs):
        text = "\n".join(msgs)
        QTimer.singleShot(0, lambda: self._detail.setText(text))

    def _update_status_signal(self, text, color):
        def _update():
            self._status_label.setText(text)
            self._status_label.setStyleSheet(f"font-size: 14px; color: {color};")
        QTimer.singleShot(0, _update)

    def _update_btn_signal(self, text, enabled):
        def _update():
            self._install_btn.setText(text)
            self._install_btn.setEnabled(enabled)
        QTimer.singleShot(0, _update)


# ============================================================
# 候选条 UI (极简细长条)
# ============================================================
class CandidateBar(QWidget):
    """极简候选条：白色背景，女书字方块 + 数字编号 + 中文注释 + 翻页"""

    def __init__(self):
        super().__init__(None)
        self._candidates = []
        self._all_candidates = []  # 所有候选
        self._page = 0             # 当前页码
        self._per_page = 8         # 每页显示数
        self._buttons = []
        self._comp_label = None
        self._page_label = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("NushuIME")
        # Tool + StaysOnTop + Frameless：不抢焦点，始终置顶
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedHeight(52)
        self.setStyleSheet("background-color: white;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        # 拼音提示
        self._comp_label = QLabel("")
        self._comp_label.setObjectName("comp")
        self._comp_label.setFixedWidth(50)
        self._comp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._comp_label)

        # 分隔线
        sep = QFrame()
        sep.setObjectName("sep")
        sep.setFixedWidth(1)
        sep.setFixedHeight(36)
        layout.addWidget(sep)

        # 候选方块（每个包含：数字编号 + 女书字 + 中文注释）
        self._buttons = []
        self._num_labels = []
        self._han_labels = []
        for i in range(8):
            cell = QWidget()
            cell.setObjectName("cell")
            cell.setFixedSize(52, 44)
            cell.setCursor(Qt.CursorShape.PointingHandCursor)
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(2, 1, 2, 1)
            cell_layout.setSpacing(0)

            # 上方：数字编号 + 女书字
            top = QHBoxLayout()
            top.setContentsMargins(0, 0, 0, 0)
            top.setSpacing(0)

            num_lbl = QLabel(str(i + 1))
            num_lbl.setObjectName("num")
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            top.addWidget(num_lbl)

            char_btn = QPushButton("")
            char_btn.setObjectName("cand")
            char_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            char_btn.clicked.connect(lambda checked, idx=i: self._click(idx))
            top.addWidget(char_btn, 1)

            cell_layout.addLayout(top, 1)

            # 下方：中文注释
            han_lbl = QLabel("")
            han_lbl.setObjectName("han")
            han_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
            cell_layout.addWidget(han_lbl)

            layout.addWidget(cell)
            self._buttons.append(char_btn)
            self._num_labels.append(num_lbl)
            self._han_labels.append(han_lbl)

        layout.addStretch()

        # 翻页按钮
        prev_btn = QPushButton("◀")
        prev_btn.setObjectName("pagebtn")
        prev_btn.setFixedSize(22, 22)
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.clicked.connect(self._prev_page)
        layout.addWidget(prev_btn)

        self._page_label = QLabel("1/1")
        self._page_label.setObjectName("pagelbl")
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setFixedWidth(36)
        layout.addWidget(self._page_label)

        next_btn = QPushButton("▶")
        next_btn.setObjectName("pagebtn")
        next_btn.setFixedSize(22, 22)
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.clicked.connect(self._next_page)
        layout.addWidget(next_btn)

        self._apply_style()
        self.hide()

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
            #comp {
                color: #333333;
                font-size: 13px;
                font-family: "Consolas", "Microsoft YaHei";
                background: transparent;
                border: none;
            }
            #sep {
                background-color: #cccccc;
                border: none;
            }
            #cell {
                background-color: #f8f8f8;
                border: 1px solid #dddddd;
                border-radius: 3px;
            }
            #cell:hover {
                background-color: #e8f0fe;
                border-color: #4285f4;
            }
            #num {
                color: #999999;
                font-size: 9px;
                font-family: "Consolas";
                background: transparent;
                border: none;
            }
            #cand {
                background: transparent;
                color: #222222;
                border: none;
                font-size: 20px;
                font-family: "Noto Traditional Nushu", "Noto Sans Nushu", "Microsoft YaHei";
                padding: 0px;
                margin: 0px;
            }
            #cand:hover {
                color: #4285f4;
            }
            #han {
                color: #888888;
                font-size: 8px;
                font-family: "Microsoft YaHei";
                background: transparent;
                border: none;
            }
            #pagebtn {
                background: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                color: #555;
                font-size: 11px;
                padding: 0px;
            }
            #pagebtn:hover {
                background: #e0e0e0;
                border-color: #999;
            }
            #pagelbl {
                color: #888;
                font-size: 10px;
                font-family: "Consolas";
                background: transparent;
                border: none;
            }
        """)

    def update_candidates(self, composition, candidates):
        self._all_candidates = candidates
        self._page = 0
        self._show_page()

    def _show_page(self):
        """显示当前页的候选"""
        total = len(self._all_candidates)
        total_pages = max(1, (total + self._per_page - 1) // self._per_page)
        start = self._page * self._per_page
        end = min(start + self._per_page, total)
        page_candidates = self._all_candidates[start:end]
        self._candidates = page_candidates

        # 更新页码
        self._page_label.setText(f"{self._page + 1}/{total_pages}")

        composition = ''  # 拼音由外部管理
        if _hook_state['composition']:
            self._comp_label.setText(_hook_state['composition'])
        elif not page_candidates:
            self._comp_label.setText("女书")
        else:
            self._comp_label.setText("")

        num = len(page_candidates)
        self.setFixedWidth(max(50 + 1 + num * 56 + 16 + 80, 200))

        for i in range(8):
            if i < num:
                self._buttons[i].setText(page_candidates[i]['char'])
                self._buttons[i].setVisible(True)
                self._num_labels[i].setVisible(True)
                # 中文注释：取第一个汉字
                hanzi = page_candidates[i].get('hanzi', '')
                first_char = hanzi[0] if hanzi else ''
                self._han_labels[i].setText(first_char)
                self._han_labels[i].setVisible(True)
                self._buttons[i].parentWidget().setVisible(True)
            else:
                self._buttons[i].setVisible(False)
                self._num_labels[i].setVisible(False)
                self._han_labels[i].setVisible(False)
                self._buttons[i].parentWidget().setVisible(False)

        self._position_near_cursor()

    def _position_near_cursor(self):
        """定位到光标附近"""
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        screen = self.screen()
        if screen:
            geo = screen.availableGeometry()
            x = min(max(pt.x - self.width() // 2, geo.x()), geo.x() + geo.width() - self.width())
            y = min(pt.y + 25, geo.y() + geo.height() - self.height())
        else:
            x = pt.x - self.width() // 2
            y = pt.y + 25
        self.move(x, y)

    def _click(self, idx):
        if idx < len(self._candidates):
            char = self._candidates[idx]['char']
            _hook_state['composition'] = ''
            self.hide()
            _send_unicode(char)

    def _next_page(self):
        total = len(self._all_candidates)
        total_pages = max(1, (total + self._per_page - 1) // self._per_page)
        if self._page < total_pages - 1:
            self._page += 1
            self._show_page()

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._show_page()

    def next_page(self):
        self._next_page()

    def prev_page(self):
        self._prev_page()


# ============================================================
# 系统托盘
# ============================================================
class SystemTrayManager(QObject):
    show_triggered = pyqtSignal()
    quit_triggered = pyqtSignal()
    mode_changed = pyqtSignal(str)
    install_font_triggered = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._mode = INPUT_MODE_NUSHU
        self._icon = None
        self._create()

    def _create(self):
        pm = QPixmap(64, 64)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(200, 50, 100))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(8, 8, 48, 48, 8, 8)
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        p.drawText(8, 8, 48, 48, Qt.AlignmentFlag.AlignCenter, "女")
        p.end()

        self._icon = QSystemTrayIcon(QIcon(pm))
        self._icon.setToolTip("女书输入法 - Nüshu IME")
        self._rebuild_menu()
        self._icon.show()

    def _rebuild_menu(self):
        m = QMenu()
        a = QAction("显示/隐藏 候选条", m)
        a.triggered.connect(self.show_triggered.emit)
        m.addAction(a)
        m.addSeparator()

        sub = QMenu("切换模式", m)
        n = QAction("𛆁𛈬 真实女书", sub)
        n.setCheckable(True); n.setChecked(self._mode == INPUT_MODE_NUSHU)
        n.triggered.connect(lambda: self._set_mode(INPUT_MODE_NUSHU))
        sub.addAction(n)
        p = QAction("拼 简化拼音", sub)
        p.setCheckable(True); p.setChecked(self._mode == INPUT_MODE_PINYIN)
        p.triggered.connect(lambda: self._set_mode(INPUT_MODE_PINYIN))
        sub.addAction(p)
        m.addMenu(sub)
        m.addSeparator()

        # 字体安装
        font_act = QAction("安装女书字体", m)
        font_act.triggered.connect(self.install_font_triggered.emit)
        m.addAction(font_act)
        m.addSeparator()

        q = QAction("退出", m)
        q.triggered.connect(self.quit_triggered.emit)
        m.addAction(q)
        self._icon.setContextMenu(m)

    def _set_mode(self, mode):
        self._mode = mode
        _hook_state['mode'] = mode
        self._rebuild_menu()
        self.mode_changed.emit(mode)

    def set_mode(self, mode):
        self._mode = mode
        _hook_state['mode'] = mode
        self._rebuild_menu()


# ============================================================
# 主应用
# ============================================================
class NvshuIME(QObject):
    _hotkey_signal = pyqtSignal()
    _type_signal = pyqtSignal(str)
    _select_signal = pyqtSignal(int)
    _cancel_signal = pyqtSignal()
    _page_signal = pyqtSignal(int)  # -1=上一页, 1=下一页

    def __init__(self, app):
        super().__init__()
        self.app = app
        self._bar = CandidateBar()
        self._tray = SystemTrayManager()
        self._nushu = NushuData()
        self._pinyin = PinyinData()
        self._hook_handle = None
        self._mode = INPUT_MODE_NUSHU

        # 信号连接（必须用 QueuedConnection，否则钩子回调被阻塞导致系统卡顿）
        QC = Qt.ConnectionType.QueuedConnection
        self._hotkey_signal.connect(self._on_hotkey, QC)
        self._type_signal.connect(self._on_type, QC)
        self._select_signal.connect(self._on_select, QC)
        self._cancel_signal.connect(self._on_cancel, QC)
        self._page_signal.connect(self._on_page, QC)
        self._tray.mode_changed.connect(self._on_mode_changed)
        self._tray.quit_triggered.connect(self.quit)
        self._tray.install_font_triggered.connect(self._install_font)

        # 安装键盘钩子
        self._install_hook()

        # 全局引用
        _hook_state['ime'] = self

        print("=" * 50)
        print("  女书输入法 v2 (Nüshu IME) 已启动")
        print("  Ctrl+Shift+N 切换女书输入模式")
        print("  系统托盘: 切换模式 / 退出")
        print("=" * 50)

    def _install_hook(self):
        """安装低层键盘钩子"""
        hook_proc = HOOKPROC(_low_level_keyboard_proc)
        # 防止 GC
        self._hook_proc_ref = hook_proc
        self._hook_handle = ctypes.windll.user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, hook_proc, None, 0
        )
        if not self._hook_handle:
            print("ERROR: 键盘钩子安装失败! 可能需要管理员权限。")
        else:
            print("键盘钩子已安装")

    def _on_hotkey(self):
        """Ctrl+N+S 触发"""
        _hook_state['active'] = not _hook_state['active']
        _hook_state['composition'] = ''
        if _hook_state['active']:
            self._bar.update_candidates('', [])
            self._bar.show()
            self._bar.raise_()
            print(">> 女书模式: 开启")
        else:
            self._bar.hide()
            print(">> 女书模式: 关闭")

    def _on_type(self, composition):
        """用户输入拼音"""
        print(f"  [输入] composition={composition}")
        if self._mode == INPUT_MODE_NUSHU:
            matches = self._nushu.search(composition)
        else:
            matches = self._pinyin.search(composition)
        print(f"  [候选] {len(matches)} 个结果")
        self._bar.update_candidates(composition, matches)
        if not self._bar.isVisible():
            self._bar.show()
            self._bar.raise_()

    def _on_select(self, idx):
        """选择候选"""
        print(f"  [选择] idx={idx} composition='{_hook_state['composition']}'")
        if self._mode == INPUT_MODE_NUSHU:
            matches = self._nushu.search(_hook_state['composition'])
        else:
            matches = self._pinyin.search(_hook_state['composition'])
        print(f"  [选择] 找到 {len(matches)} 个候选")
        if 0 <= idx < len(matches):
            char = matches[idx]['char']
            _hook_state['composition'] = ''
            self._bar.hide()
            _send_unicode(char)

    def _on_cancel(self):
        """取消输入"""
        _hook_state['composition'] = ''
        self._bar.hide()

    def _on_page(self, direction):
        """翻页 direction: -1=上一页, 1=下一页"""
        if direction < 0:
            self._bar.prev_page()
        else:
            self._bar.next_page()

    def _on_mode_changed(self, mode):
        self._mode = mode
        _hook_state['mode'] = mode
        print(f"切换到: {'真实女书' if mode == INPUT_MODE_NUSHU else '简化拼音'}")

    def _install_font(self):
        """弹出字体安装对话框"""
        self._font_dlg = FontInstallDialog()
        self._font_dlg.show()

    def quit(self):
        print("正在退出...")
        if self._hook_handle:
            ctypes.windll.user32.UnhookWindowsHookEx(self._hook_handle)
            self._hook_handle = None
        _hook_state['ime'] = None
        _hook_state['active'] = False
        self._bar.close()
        self._tray._icon.hide()
        self.app.quit()


# ============================================================
# 字体管理
# ============================================================
class FontManager:
    URL = "https://notofonts.github.io/nushu/fonts/NotoTraditionalNushu/unhinted/ttf/NotoTraditionalNushu-Regular.ttf"
    NAME = "NotoTraditionalNushu-Regular.ttf"

    @classmethod
    def ensure(cls):
        app_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        fp = app_dir / "fonts" / cls.NAME

        # 下载字体（如果不存在）
        if not fp.exists():
            sf = Path(os.environ.get('WINDIR', 'C:/Windows')) / "Fonts" / cls.NAME
            if not sf.exists():
                try:
                    print("正在下载女书字体...")
                    fd = app_dir / "fonts"; fd.mkdir(exist_ok=True)
                    urllib.request.urlretrieve(cls.URL, str(fd / cls.NAME))
                    print("字体下载完成")
                except Exception as e:
                    print(f"字体下载失败: {e}")
                    return

        # 注册本地字体到当前会话（不需要管理员权限）
        if fp.exists():
            ctypes.windll.gdi32.AddFontResourceW(str(fp))
            print(f"本地字体已注册: {fp}")

        # 通知系统字体变更
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x001D, 0, 0)


def main():
    # 启用输出刷新，确保调试信息实时显示
    sys.stdout.reconfigure(line_buffering=True)

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 下载字体
    threading.Thread(target=FontManager.ensure, daemon=True).start()

    ime = NvshuIME(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()