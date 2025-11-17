from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ErrorType(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DX = "dx"  # Developer Experience
    DESIGN = "design"
    ARCHITECTURE = "architecture"


class Experience(BaseModel):
    """
    Modelo para armazenar experiências de erro/aprendizado.
    Versionado para suportar migrations futuras.
    """
    project_id: str = Field(..., description="ID do projeto")
    module: str = Field(..., description="Módulo ou componente afetado")
    stack: str = Field(..., description="Stack tecnológico (ex: python+fastapi+react)")
    
    # Metadados de severidade e impacto
    schema_version: str = Field(default="1.0", description="Versão do schema")
    severity: SeverityLevel = Field(..., description="Nível de severidade")
    affected_components: List[str] = Field(default_factory=list, description="Componentes afetados")
    tags: List[str] = Field(default_factory=list, description="Tags para categorização")
    resolution_time_minutes: Optional[int] = Field(None, description="Tempo de resolução em minutos")
    
    # Detalhes do problema
    error_type: ErrorType = Field(..., description="Tipo de erro")
    summary: str = Field(..., description="Resumo do problema")
    root_cause: str = Field(..., description="Causa raiz")
    fix_applied: str = Field(..., description="Solução aplicada")
    
    # Exemplos de código (opcional)
    bad_snippet: Optional[str] = Field(None, description="Exemplo de código problemático")
    good_snippet: Optional[str] = Field(None, description="Exemplo de código corrigido")
    
    # Metadados temporais
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(None)
    
    # Campos para análise
    llm_comment: Optional[str] = Field(None, description="Comentário do LLM sobre o aprendizado")
    lesson_extracted: Optional[str] = Field(None, description="Lição principal extraída")


class Lesson(BaseModel):
    """
    Lição aprendida extraída de experiências.
    """
    rule: str = Field(..., description="Regra ou princípio")
    rationale: str = Field(..., description="Justificativa ou explicação")
    example_bad: Optional[str] = Field(None, description="Exemplo do que não fazer")
    example_good: Optional[str] = Field(None, description="Exemplo do que fazer")
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM, description="Severidade da lição")
    context: Optional[str] = Field(None, description="Contexto onde a lição se aplica")


class LessonsBundle(BaseModel):
    """
    Conjunto de lições organizadas por categoria.
    """
    project_id: str
    module: Optional[str] = None
    stack: str
    high_level_rules: List[Lesson] = Field(default_factory=list)
    code_smells_to_avoid: List[Lesson] = Field(default_factory=list)
    security_pitfalls: List[Lesson] = Field(default_factory=list)
    performance_tips: List[Lesson] = Field(default_factory=list)
    design_patterns: List[Lesson] = Field(default_factory=list)
    
    # Metadados
    total_lessons: int = Field(default=0, description="Total de lições no bundle")
    relevance_score: float = Field(default=0.0, description="Score de relevância para a query")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DecisionLog(BaseModel):
    """
    Registro de decisões arquitetônicas importantes.
    """
    project_id: str
    module: str
    decision_type: Literal["architecture", "technology", "pattern", "refactor"]
    decision: str = Field(..., description="Decisão tomada")
    rationale: str = Field(..., description="Razão da decisão")
    alternatives_considered: List[str] = Field(default_factory=list)
    impact_assessment: Optional[str] = Field(None)
    made_at: datetime = Field(default_factory=datetime.utcnow)
    made_by: Optional[str] = Field(None, description="Agente ou pessoa que tomou a decisão")


class MemoryStats(BaseModel):
    """
    Estatísticas do sistema de memória.
    """
    total_experiences: int
    by_severity: Dict[str, int]
    by_error_type: Dict[str, int]
    by_project: Dict[str, int]
    avg_lessons_per_task: float
    memory_hit_rate: float
    lesson_reuse_rate: float
    deduplication_stats: Dict[str, Any]
    cache_performance: Dict[str, float]
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ConsolidatedLesson(BaseModel):
    """
    Meta-lição consolidada de múltiplas experiências similares.
    """
    rule: str = Field(..., description="Regra consolidada")
    frequency: int = Field(..., description="Quantas experiências originaram esta lição")
    severity_distribution: Dict[str, int] = Field(..., description="Distribuição de severidade")
    contexts: List[str] = Field(..., description="Contextos onde se aplica")
    examples: List[str] = Field(default_factory=list, description="Exemplos práticos")
    confidence_score: float = Field(..., description="Confiança na regra (0-1)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source_experiences: List[str] = Field(..., description="IDs das experiências originais")


class MemoryQuery(BaseModel):
    """
    Query para busca de experiências relevantes.
    """
    spec: str = Field(..., description="Especificação da tarefa atual")
    stack: str = Field(..., description="Stack tecnológico")
    module: Optional[str] = Field(None, description="Módulo específico")
    severity_filter: Optional[List[SeverityLevel]] = Field(None, description="Filtro por severidade")
    error_types: Optional[List[ErrorType]] = Field(None, description="Filtro por tipo de erro")
    tags: Optional[List[str]] = Field(None, description="Filtro por tags")
    limit: int = Field(default=10, description="Limite de resultados")
    include_examples: bool = Field(default=True, description="Incluir exemplos de código")


class DeduplicationResult(BaseModel):
    """
    Resultado da operação de deduplicação.
    """
    duplicates_found: int
    duplicates_removed: int
    experiences_kept: int
    time_saved_minutes: int
    memory_freed_mb: float
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class PruningResult(BaseModel):
    """
    Resultado da operação de pruning (limpeza) de memórias.
    """
    total_evaluated: int
    experiences_removed: int
    critical_kept: int
    high_kept: int
    medium_removed: int
    low_removed: int
    memory_freed_mb: float
    cutoff_days: int
    processed_at: datetime = Field(default_factory=datetime.utcnow)