# -*- coding: utf-8 -*-
"""
服务注册中心 - 统一管理全局服务实例
"""


class ServiceRegistry:
    """服务注册中心"""

    _llm_service = None
    _code_service = None

    @classmethod
    def get_llm_service(cls):
        if cls._llm_service is None:
            from services.llm_service import LLMService
            cls._llm_service = LLMService()
        return cls._llm_service

    @classmethod
    def get_code_service(cls):
        if cls._code_service is None:
            from services.code_service import CodeService
            from services.vector_service import get_vector_service
            llm = cls.get_llm_service()
            vector = get_vector_service()
            cls._code_service = CodeService(llm, vector)
        return cls._code_service
