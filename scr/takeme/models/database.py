from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# 根据数据库类型选择是否加 SQLite 特殊参数
if "sqlite" in settings.database_url:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(settings.database_url)  # MySQL/PostgreSQL

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from models.game_model import Base
    Base.metadata.create_all(bind=engine)

    # 插入测试 POI（如果表为空）
    from models.poi_model import POI
    db = SessionLocal()
    try:
        if db.query(POI).count() == 0:
            mock_pois = [
                POI(poi_uid="p_001", name="成都远洋太古里", type="商业街", lng=104.091122, lat=30.658688),
                POI(poi_uid="p_002", name="宽窄巷子", type="景点", lng=104.059491, lat=30.669532),
                POI(poi_uid="p_003", name="锦里", type="景点", lng=104.053633, lat=30.648847),
                POI(poi_uid="p_004", name="大熊猫繁育研究基地", type="景点", lng=104.150032, lat=30.734611),
                POI(poi_uid="p_005", name="春熙路", type="商业街", lng=104.084170, lat=30.657680),
                POI(poi_uid="p_006", name="武侯祠", type="景点", lng=104.048656, lat=30.644421),
                POI(poi_uid="p_007", name="蜀大侠火锅(春熙路店)", type="餐饮", lng=104.085200, lat=30.655500),
                POI(poi_uid="p_008", name="小龙坎老火锅(概念店)", type="餐饮", lng=104.062000, lat=30.670000),
            ]
            db.add_all(mock_pois)
            db.commit()
    finally:
        db.close()