"""WGS-84 → BD-09 坐标转换"""
import math

_PI = math.pi
_A = 6378245.0  # 长半轴
_EE = 0.00669342162296594323  # 偏心率平方


def _out_of_china(lng: float, lat: float) -> bool:
    return lng < 72.004 or lng > 137.8347 or lat < 0.8293 or lat > 55.8271


def _transform_lat(lng: float, lat: float) -> float:
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * _PI) + 20.0 * math.sin(2.0 * lng * _PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * _PI) + 40.0 * math.sin(lat / 3.0 * _PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * _PI) + 320 * math.sin(lat * _PI / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(lng: float, lat: float) -> float:
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * _PI) + 20.0 * math.sin(2.0 * lng * _PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * _PI) + 40.0 * math.sin(lng / 3.0 * _PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * _PI) + 300.0 * math.sin(lng / 30.0 * _PI)) * 2.0 / 3.0
    return ret


def wgs84_to_gcj02(lng: float, lat: float) -> tuple:
    """WGS-84 → GCJ-02（火星坐标系）"""
    if _out_of_china(lng, lat):
        return lng, lat
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * _PI
    magic = math.sin(radlat)
    magic = 1 - _EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((_A * (1 - _EE)) / (magic * sqrtmagic) * _PI)
    dlng = (dlng * 180.0) / (_A / sqrtmagic * math.cos(radlat) * _PI)
    return lng + dlng, lat + dlat


def gcj02_to_bd09(lng: float, lat: float) -> tuple:
    """GCJ-02 → BD-09（百度坐标系）"""
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * _PI * 3000.0 / 180.0)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * _PI * 3000.0 / 180.0)
    return z * math.cos(theta) + 0.0065, z * math.sin(theta) + 0.006


def wgs84_to_bd09(lng: float, lat: float) -> tuple:
    """WGS-84 → BD-09（一步到位）"""
    gcj = wgs84_to_gcj02(lng, lat)
    return gcj02_to_bd09(*gcj)