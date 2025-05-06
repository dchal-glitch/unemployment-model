# -*- coding: utf-8 -*-
"""
Database connection utilities for the unemployment forecast model.
"""
from dotenv import load_dotenv
load_dotenv()
import os
import cx_Oracle
from sqlalchemy import create_engine

class DBConfig:
    """Database configuration parameters"""
    def __init__(self):
        # connection parameters

        self.host = os.getenv('DB_HOST')
        self.port = os.getenv('DB_PORT')
        self.service_name = os.getenv('DB_SERVICE_NAME')
        self.password = os.getenv('DB_PASSWORD')
        self.userLD_POP = 'LD_COI_POP_DEMOGRAPHY'
        self.userS_POP = 'S_COI_POP_DEMOGRAPHY'
        self.userLD_ECON = 'LD_COI_ECONOMY'
        self.userSE_ECON = 'S_COI_ECONOMY'
        self.user_KPI = 'LD_COI_STAT'
        self.user_MISC = 'LD_COI_MISC'
        self.userS_JobVac = 'S_COI_LABOUR_FORCE'
        self.userSDWH = 'SC_ENT_DWH'
        self.user_SC = 'SC_ENT_DWH'


def get_db_config():
    """Returns a database configuration object"""
    return DBConfig()


def database_engine_user(user, db_config=None):
    """
    Create a SQLAlchemy engine for the specified user
    
    Args:
        user: Database user name
        db_config: Optional database configuration object
        
    Returns:
        SQLAlchemy engine
    """
    if db_config is None:
        db_config = get_db_config()
        
    oracle_connection_string = (
            'oracle+cx_oracle://{username}:{password}@' +
            cx_Oracle.makedsn('{hostname}', '{port}', service_name='{service_name}')
    )

    engine = create_engine(
        oracle_connection_string.format(
            username=user,
            password=db_config.password,
            hostname=db_config.host,
            port=db_config.port,
            service_name=db_config.service_name,
        )
    )
    return engine


def database_connection_user(user, db_config=None):
    """
    Create a cx_Oracle connection and cursor for the specified user
    
    Args:
        user: Database user name
        db_config: Optional database configuration object
        
    Returns:
        Tuple of (connection, cursor)
    """
    if db_config is None:
        db_config = get_db_config()
        
    dsn_tns = cx_Oracle.makedsn(db_config.host, db_config.port, service_name=db_config.service_name)
    conn = cx_Oracle.connect(user=user, password=db_config.password, dsn=dsn_tns, encoding="UTF-8")
    c = conn.cursor()
    return conn, c
