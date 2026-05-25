from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import UUID
import logging
import traceback

from app.workers.celery_app import celery_app
from app.config import settings
from app.models.job import Job, JobStatus
from app.models.design import Design, DesignStatus
from app.workers.steps.step1_upscale import upscale_image
from app.workers.steps.step2_segment import segment_image
from app.workers.steps.step3_colorcluster import cluster_colors
from app.workers.steps.step4_layerbuild import build_layer_file
from app.workers.steps.step5_colorways import generate_colorways
from app.workers.steps.step6_export import export_master_tiff

logger = logging.getLogger(__name__)

sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
SessionLocal = sessionmaker(bind=sync_engine)


class DatabaseTask(Task):
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True)
def process_design(self, job_id: str):
    db = self.db
    
    try:
        job = db.query(Job).filter(Job.id == UUID(job_id)).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        design = db.query(Design).filter(Design.id == job.design_id).first()
        if not design:
            logger.error(f"Design {job.design_id} not found")
            return
        
        logger.info(f"Starting processing for job {job_id}, design {design.id}")
        
        job.status = JobStatus.UPSCALING
        job.current_step = 1
        design.status = DesignStatus.PROCESSING
        db.commit()
        
        logger.info("Step 1: Upscaling image...")
        upscaled_path = upscale_image(design, db)
        design.upscaled_storage_path = upscaled_path
        job.current_step = 1
        db.commit()
        
        job.status = JobStatus.SEGMENTING
        job.current_step = 2
        db.commit()
        
        logger.info("Step 2: Segmenting image...")
        masks = segment_image(design, db)
        job.current_step = 2
        db.commit()
        
        job.status = JobStatus.CLUSTERING
        job.current_step = 3
        db.commit()
        
        logger.info("Step 3: Clustering colors...")
        clusters = cluster_colors(design, masks, db)
        job.current_step = 3
        db.commit()
        
        job.status = JobStatus.BUILDING
        job.current_step = 4
        db.commit()
        
        logger.info("Step 4: Building layers...")
        layers = build_layer_file(design, clusters, db)
        job.current_step = 4
        db.commit()
        
        job.status = JobStatus.BUILDING
        job.current_step = 5
        db.commit()
        
        logger.info("Step 5: Exporting master TIFF...")
        export_master_tiff(design, layers, db)
        job.current_step = 5
        db.commit()
        
        job.status = JobStatus.GENERATING
        job.current_step = 6
        db.commit()
        
        logger.info("Step 6: Generating colorways...")
        generate_colorways(design, layers, db)
        job.current_step = 6
        db.commit()
        
        job.status = JobStatus.DONE
        job.completed_at = db.query(Job).filter(Job.id == job.id).first().created_at
        design.status = DesignStatus.REVIEW
        db.commit()
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        try:
            job = db.query(Job).filter(Job.id == UUID(job_id)).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                
                design = db.query(Design).filter(Design.id == job.design_id).first()
                if design:
                    design.status = DesignStatus.UPLOADED
                
                db.commit()
        except Exception as commit_error:
            logger.error(f"Error updating job status: {str(commit_error)}")
            db.rollback()


@celery_app.task(base=DatabaseTask, bind=True)
def generate_colorways_task(self, design_id: str):
    db = self.db
    
    try:
        design = db.query(Design).filter(Design.id == UUID(design_id)).first()
        if not design:
            logger.error(f"Design {design_id} not found")
            return
        
        from app.models.layer import Layer
        layers = db.query(Layer).filter(Layer.design_id == design.id).all()
        
        generate_colorways(design, layers, db)
        
        logger.info(f"Colorways generated for design {design_id}")
        
    except Exception as e:
        logger.error(f"Error generating colorways for design {design_id}: {str(e)}")
        logger.error(traceback.format_exc())


@celery_app.task(base=DatabaseTask, bind=True)
def create_manual_colorway_task(self, design_id: str, name: str, color_map: dict):
    db = self.db
    
    try:
        design = db.query(Design).filter(Design.id == UUID(design_id)).first()
        if not design:
            logger.error(f"Design {design_id} not found")
            return
        
        from app.models.layer import Layer
        from app.workers.steps.step5_colorways import create_single_colorway
        
        layers = db.query(Layer).filter(Layer.design_id == design.id).all()
        
        create_single_colorway(design, layers, name, color_map, "manual", db)
        
        logger.info(f"Manual colorway '{name}' created for design {design_id}")
        
    except Exception as e:
        logger.error(f"Error creating manual colorway for design {design_id}: {str(e)}")
        logger.error(traceback.format_exc())
