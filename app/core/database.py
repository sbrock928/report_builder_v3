# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import os

# SQLite database paths
DW_DATABASE_PATH = os.getenv("DW_DATABASE_PATH", "./data_warehouse.db")
CONFIG_DATABASE_PATH = os.getenv("CONFIG_DATABASE_PATH", "./config.db")

# SQLite connection URLs
DW_DATABASE_URL = f"sqlite:///{DW_DATABASE_PATH}"
CONFIG_DATABASE_URL = f"sqlite:///{CONFIG_DATABASE_PATH}"

# Data Warehouse Engine (for data queries)
dw_engine = create_engine(DW_DATABASE_URL, connect_args={"check_same_thread": False})
DWSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dw_engine)
DWBase = declarative_base()

# Config Database Engine (for calculations, report templates, etc.)
config_engine = create_engine(CONFIG_DATABASE_URL, connect_args={"check_same_thread": False})
ConfigSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=config_engine)
ConfigBase = declarative_base()

def get_dw_session() -> Session:
    """Dependency to get data warehouse database session"""
    db = DWSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_config_session() -> Session:
    """Dependency to get config database session"""
    db = ConfigSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database initialization
def create_all_tables():
    """Create all tables in both databases"""
    # Create DW tables
    DWBase.metadata.create_all(bind=dw_engine)
    
    # Create Config tables
    ConfigBase.metadata.create_all(bind=config_engine)

def seed_sample_data():
    """Seed sample data into the data warehouse for testing"""
    from app.datawarehouse.models import Deal, Tranche, TrancheBal
    
    dw_db = DWSessionLocal()
    try:
        # Check if data already exists
        existing_deal = dw_db.query(Deal).first()
        if existing_deal:
            return
        
        # Create sample deals
        deals = [
            Deal(dl_nbr=101, issr_cde="ISSUER001", cdi_file_nme="CDI001", CDB_cdi_file_nme="CDB001"),
            Deal(dl_nbr=102, issr_cde="ISSUER002", cdi_file_nme="CDI002", CDB_cdi_file_nme="CDB002"),
            Deal(dl_nbr=103, issr_cde="ISSUER003", cdi_file_nme="CDI003", CDB_cdi_file_nme="CDB003"),
        ]
        
        for deal in deals:
            dw_db.add(deal)
        
        dw_db.commit()
        
        # Create sample tranches
        tranches = [
            # Deal 101 tranches
            Tranche(dl_nbr=101, tr_id="A", tr_cusip_id="CUSIP101A"),
            Tranche(dl_nbr=101, tr_id="B", tr_cusip_id="CUSIP101B"),
            Tranche(dl_nbr=101, tr_id="C", tr_cusip_id="CUSIP101C"),
            
            # Deal 102 tranches
            Tranche(dl_nbr=102, tr_id="A", tr_cusip_id="CUSIP102A"),
            Tranche(dl_nbr=102, tr_id="B", tr_cusip_id="CUSIP102B"),
            
            # Deal 103 tranches
            Tranche(dl_nbr=103, tr_id="A", tr_cusip_id="CUSIP103A"),
            Tranche(dl_nbr=103, tr_id="B", tr_cusip_id="CUSIP103B"),
            Tranche(dl_nbr=103, tr_id="C", tr_cusip_id="CUSIP103C"),
            Tranche(dl_nbr=103, tr_id="D", tr_cusip_id="CUSIP103D"),
        ]
        
        for tranche in tranches:
            dw_db.add(tranche)
        
        dw_db.commit()
        
        # Create sample tranche balance data
        import random
        tranche_bals = []
        
        for tranche in tranches:
            for cycle in [202401, 202402, 202403, 202404]:
                # Generate realistic financial data
                end_bal = random.uniform(1000000, 50000000)  # $1M to $50M
                pass_thru_rate = random.uniform(0.02, 0.08)  # 2% to 8%
                
                tranche_bal = TrancheBal(
                    dl_nbr=tranche.dl_nbr,
                    tr_id=tranche.tr_id,
                    cycle_cde=cycle,
                    tr_end_bal_amt=round(end_bal, 2),
                    tr_prin_rel_ls_amt=round(random.uniform(0, end_bal * 0.1), 2),
                    tr_pass_thru_rte=round(pass_thru_rate, 6),
                    tr_accrl_days=random.randint(28, 31),
                    tr_int_dstrb_amt=round(end_bal * pass_thru_rate / 12, 2),
                    tr_prin_dstrb_amt=round(random.uniform(0, end_bal * 0.05), 2),
                    tr_int_accrl_amt=round(end_bal * pass_thru_rate / 12, 2),
                    tr_int_shtfl_amt=round(random.uniform(0, 1000), 2)
                )
                tranche_bals.append(tranche_bal)
        
        for tranche_bal in tranche_bals:
            dw_db.add(tranche_bal)
        
        dw_db.commit()
        print(f"Seeded {len(deals)} deals, {len(tranches)} tranches, and {len(tranche_bals)} tranche balance records")
        
    except Exception as e:
        dw_db.rollback()
        print(f"Error seeding sample data: {e}")
        raise e
    finally:
        dw_db.close()

def seed_default_calculations():
    """Seed the database with default calculations"""
    from app.config.models import Calculation
    
    config_db = ConfigSessionLocal()
    try:
        # Check if calculations already exist
        existing = config_db.query(Calculation).first()
        if existing:
            return
        
        # Default calculations using actual TrancheBal fields
        default_calcs = [
            Calculation(
                name="total_ending_balance",
                description="Sum of tranche ending balance amounts",
                formula="SUM(tb.tr_end_bal_amt)",
                aggregation_method="SUM",
                source_tables=["tranchebal tb"],
                created_by="system"
            ),
            Calculation(
                name="total_principal_released",
                description="Sum of principal release losses",
                formula="SUM(tb.tr_prin_rel_ls_amt)",
                aggregation_method="SUM",
                source_tables=["tranchebal tb"],
                created_by="system"
            ),
            Calculation(
                name="weighted_avg_pass_thru_rate",
                description="Weighted average pass-through rate",
                formula="SUM(tb.tr_end_bal_amt * tb.tr_pass_thru_rte) / NULLIF(SUM(tb.tr_end_bal_amt), 0)",
                aggregation_method="WEIGHTED_AVG",
                source_tables=["tranchebal tb"],
                created_by="system"
            ),
            Calculation(
                name="total_interest_distribution",
                description="Sum of interest distribution amounts",
                formula="SUM(tb.tr_int_dstrb_amt)",
                aggregation_method="SUM",
                source_tables=["tranchebal tb"],
                created_by="system"
            ),
            Calculation(
                name="total_principal_distribution",
                description="Sum of principal distribution amounts",
                formula="SUM(tb.tr_prin_dstrb_amt)",
                aggregation_method="SUM",
                source_tables=["tranchebal tb"],
                created_by="system"
            ),
            Calculation(
                name="total_interest_accrued",
                description="Sum of interest accrual amounts",
                formula="SUM(tb.tr_int_accrl_amt)",
                aggregation_method="SUM",
                source_tables=["tranchebal tb"],
                created_by="system"
            ),
            Calculation(
                name="total_interest_shortfall",
                description="Sum of interest shortfall amounts",
                formula="SUM(tb.tr_int_shtfl_amt)",
                aggregation_method="SUM",
                source_tables=["tranchebal tb"],
                created_by="system"
            ),
            Calculation(
                name="avg_accrual_days",
                description="Average accrual days across tranches",
                formula="AVG(CAST(tb.tr_accrl_days AS FLOAT))",
                aggregation_method="AVG",
                source_tables=["tranchebal tb"],
                created_by="system"
            ),
            Calculation(
                name="tranche_count",
                description="Number of tranches",
                formula="COUNT(DISTINCT t.tr_id)",
                aggregation_method="COUNT",
                source_tables=["tranche t"],
                created_by="system"
            ),
            Calculation(
                name="avg_ending_balance",
                description="Average ending balance per tranche",
                formula="AVG(tb.tr_end_bal_amt)",
                aggregation_method="AVG",
                source_tables=["tranchebal tb"],
                created_by="system"
            )
        ]
        
        for calc in default_calcs:
            config_db.add(calc)
        
        config_db.commit()
        print(f"Seeded {len(default_calcs)} default calculations")
        
    except Exception as e:
        config_db.rollback()
        print(f"Error seeding default calculations: {e}")
        raise e
    finally:
        config_db.close()