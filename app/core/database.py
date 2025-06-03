# app/core/database.py - Updated with cycle migration
"""Database configuration with cycle_code moved to execution logs"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator
import os

# Create declarative bases
DWBase = declarative_base()
ConfigBase = declarative_base()

# Database file paths
DW_DATABASE_PATH = os.getenv("DW_DATABASE_PATH", "./data_warehouse.db")
CONFIG_DATABASE_PATH = os.getenv("CONFIG_DATABASE_PATH", "./config.db")

# Create engines
def create_dw_engine():
    return create_engine(f"sqlite:///{DW_DATABASE_PATH}", echo=False)

def create_config_engine():
    return create_engine(f"sqlite:///{CONFIG_DATABASE_PATH}", echo=False)

# Session makers
DWSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=create_dw_engine())
ConfigSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=create_config_engine())

def get_dw_session() -> Generator[Session, None, None]:
    """Get data warehouse database session"""
    db = DWSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_config_session() -> Generator[Session, None, None]:
    """Get config database session"""
    db = ConfigSessionLocal()
    try:
        yield db
    finally:
        db.close()

async def create_dw_tables():
    """Create data warehouse database tables"""
    # Import models to register them with the base
    from app.features.datawarehouse.models import Deal, Tranche, TrancheBal
    
    engine = create_dw_engine()
    DWBase.metadata.create_all(bind=engine)

async def create_config_tables():
    """Create config database tables"""
    # Import models to register them with the base - ORDER MATTERS for relationships
    from app.features.calculations.models import Calculation
    from app.features.reports.models import Report, ReportDeal, ReportTranche, ReportCalculation, ReportExecutionLog
    
    engine = create_config_engine()
    ConfigBase.metadata.create_all(bind=engine)

async def seed_sample_data():
    """Seed sample data into data warehouse (unchanged)"""
    from app.features.datawarehouse.models import Deal, Tranche, TrancheBal
    import random
    
    db = DWSessionLocal()
    try:
        # Check if data already exists
        existing_deals = db.query(Deal).count()
        if existing_deals > 0:
            print(f"Sample data already exists ({existing_deals} deals found), skipping seeding")
            return

        # Create 50 sample deals with varying characteristics
        deals = []
        issuers = ["FNMA", "FHLMC", "GNMA", "PRIVATE", "AGENCY", "JUMBO", "PRIME", "SUBPRIME"]
        
        for i in range(1, 51):  # Create 50 deals (101-150)
            deal_num = 100 + i
            issuer = random.choice(issuers)
            deals.append(Deal(
                dl_nbr=deal_num,
                issr_cde=f"{issuer}{i:03d}",
                cdi_file_nme=f"CDI_{issuer}_{deal_num}",
                CDB_cdi_file_nme=f"CDB_{issuer}_{deal_num}"
            ))
        
        for deal in deals:
            db.add(deal)
        
        db.commit()
        print(f"Created {len(deals)} deals")
        
        # Create tranches with varying structures per deal
        tranches = []
        tranche_structures = [
            ['A1', 'A2', 'B', 'C'],           # Standard 4-tranche
            ['A', 'B', 'C'],                  # Simple 3-tranche
            ['A1', 'A2', 'A3', 'B', 'C'],     # Complex 5-tranche
            ['A', 'B'],                       # Simple 2-tranche
            ['A1', 'A2', 'B1', 'B2', 'C'],   # Complex mixed
            ['SR', 'A', 'B'],                 # Senior/Sub structure
        ]
        
        for deal in deals:
            # Randomly select a tranche structure
            structure = random.choice(tranche_structures)
            
            for tr_id in structure:
                tranches.append(Tranche(
                    tr_id=tr_id,
                    dl_nbr=deal.dl_nbr,
                    tr_cusip_id=f"{deal.issr_cde[:4]}{deal.dl_nbr}{tr_id}"
                ))
        
        for tranche in tranches:
            db.add(tranche)
        
        db.commit()
        print(f"Created {len(tranches)} tranches")
        
        # Create 24 months of historical data (Jan 2023 - Dec 2024)
        tranche_balances = []
        cycles = []
        
        # Generate cycle codes for 24 months
        for year in [2023, 2024]:
            for month in range(1, 13):
                cycles.append(year * 100 + month)  # 202301, 202302, ..., 202412
        
        # Rating-based multipliers for more realistic data
        rating_multipliers = {
            'A1': {'balance': 1.5, 'rate': 0.02},    # Larger, lower rate
            'A2': {'balance': 1.3, 'rate': 0.025},
            'A3': {'balance': 1.1, 'rate': 0.03},
            'A': {'balance': 1.2, 'rate': 0.025},
            'B1': {'balance': 0.8, 'rate': 0.035},
            'B2': {'balance': 0.6, 'rate': 0.04},
            'B': {'balance': 0.7, 'rate': 0.035},
            'C': {'balance': 0.4, 'rate': 0.05},     # Smaller, higher rate
            'SR': {'balance': 2.0, 'rate': 0.015},   # Senior, large, low rate
        }
        
        for tranche in tranches:
            # Get multiplier based on tranche rating
            multiplier = rating_multipliers.get(tranche.tr_id, {'balance': 1.0, 'rate': 0.03})
            
            # Base amounts that will vary over time
            base_balance = 1000000.0 * multiplier['balance']
            base_rate = multiplier['rate']
            
            for i, cycle in enumerate(cycles):
                # Simulate amortization (declining balances over time)
                amortization_factor = max(0.1, 1.0 - (i * 0.02))  # Decline 2% per month
                
                # Add some randomness
                balance_variance = random.uniform(0.9, 1.1)
                rate_variance = random.uniform(0.95, 1.05)
                
                current_balance = base_balance * amortization_factor * balance_variance
                current_rate = base_rate * rate_variance
                
                # Calculate related amounts
                principal_release = current_balance * random.uniform(0.01, 0.05)  # 1-5% of balance
                interest_dist = current_balance * current_rate / 12  # Monthly interest
                principal_dist = current_balance * random.uniform(0.02, 0.08)  # 2-8% monthly principal
                
                tranche_balances.append(TrancheBal(
                    tr_id=tranche.tr_id,
                    dl_nbr=tranche.dl_nbr,
                    cycle_cde=cycle,
                    tr_end_bal_amt=round(current_balance, 2),
                    tr_prin_rel_ls_amt=round(principal_release, 2),
                    tr_pass_thru_rte=round(current_rate, 6),
                    tr_int_dstrb_amt=round(interest_dist, 2),
                    tr_prin_dstrb_amt=round(principal_dist, 2),
                    tr_int_accrl_amt=round(interest_dist * 1.05, 2),  # Slightly higher accrual
                    tr_int_shtfl_amt=round(interest_dist * 0.02, 2),  # 2% shortfall
                    tr_accrl_days=random.randint(28, 31)  # Days in month
                ))
        
        # Batch insert for better performance
        batch_size = 1000
        for i in range(0, len(tranche_balances), batch_size):
            batch = tranche_balances[i:i + batch_size]
            for tranche_bal in batch:
                db.add(tranche_bal)
            db.commit()
            print(f"Inserted batch {i//batch_size + 1} of {(len(tranche_balances) + batch_size - 1) // batch_size}")
        
        print(f"Seeded {len(deals)} deals, {len(tranches)} tranches, and {len(tranche_balances)} tranche balance records across {len(cycles)} months")
        print(f"Date range: {min(cycles)} to {max(cycles)}")
        print(f"Average tranches per deal: {len(tranches) / len(deals):.1f}")
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

async def seed_default_calculations():
    """Seed default calculations in new ORM-based format"""
    from app.features.calculations.models import Calculation, AggregationFunction, SourceModel, GroupLevel
    
    config_db = ConfigSessionLocal()
    try:
        # Check if calculations already exist
        existing_count = config_db.query(Calculation).count()
        if existing_count > 0:
            print(f"Calculations already exist ({existing_count} found), skipping seeding")
            return

        # Default calculations using ORM-based approach
        default_calcs = [
            Calculation(
                name="Total Ending Balance",
                description="Sum of tranche ending balance amounts",
                aggregation_function=AggregationFunction.SUM,
                source_model=SourceModel.TRANCHE_BAL,
                source_field="tr_end_bal_amt",
                group_level=GroupLevel.DEAL,
                created_by="system"
            ),
            Calculation(
                name="Total Principal Distribution",
                description="Sum of principal distribution amounts",
                aggregation_function=AggregationFunction.SUM,
                source_model=SourceModel.TRANCHE_BAL,
                source_field="tr_prin_dstrb_amt",
                group_level=GroupLevel.DEAL,
                created_by="system"
            ),
            Calculation(
                name="Total Interest Distribution",
                description="Sum of interest distribution amounts",
                aggregation_function=AggregationFunction.SUM,
                source_model=SourceModel.TRANCHE_BAL,
                source_field="tr_int_dstrb_amt",
                group_level=GroupLevel.DEAL,
                created_by="system"
            ),
            Calculation(
                name="Tranche Ending Balance",
                description="Ending balance amount at tranche level",
                aggregation_function=AggregationFunction.SUM,
                source_model=SourceModel.TRANCHE_BAL,
                source_field="tr_end_bal_amt",
                group_level=GroupLevel.TRANCHE,
                created_by="system"
            ),
            Calculation(
                name="Weighted Average Pass Through Rate",
                description="Balance-weighted average pass-through rate",
                aggregation_function=AggregationFunction.WEIGHTED_AVG,
                source_model=SourceModel.TRANCHE_BAL,
                source_field="tr_pass_thru_rte",
                weight_field="tr_end_bal_amt",
                group_level=GroupLevel.DEAL,
                created_by="system"
            ),
            Calculation(
                name="Average Accrual Days",
                description="Average accrual days per deal",
                aggregation_function=AggregationFunction.AVG,
                source_model=SourceModel.TRANCHE_BAL,
                source_field="tr_accrl_days",
                group_level=GroupLevel.DEAL,
                created_by="system"
            ),
            Calculation(
                name="Tranche Count",
                description="Count of tranches per deal",
                aggregation_function=AggregationFunction.COUNT,
                source_model=SourceModel.TRANCHE,
                source_field="tr_id",
                group_level=GroupLevel.DEAL,
                created_by="system"
            )
        ]

        for calc in default_calcs:
            config_db.add(calc)
        
        config_db.commit()
        print(f"Seeded {len(default_calcs)} default calculations")
        
    except Exception as e:
        config_db.rollback()
        raise e
    finally:
        config_db.close()