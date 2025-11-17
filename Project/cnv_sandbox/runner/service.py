from utils.module_utils import modulize_name, load_module, get_class_from_module


class RunnerService:
    @staticmethod
    def run_algorithm(
        algorithm_id: str,
        input_cls: str,
        exe_cls: str,
        bam: bytes,
        input_data: dict,
        **kwargs,
    ) -> dict:
        """Run an installed algorithm.
        This method executes the algorithm specified by the name, input_cls, and exe_cls.
        It takes the BAM file and input data as parameters and returns the output.
        """
        algorithm_id = modulize_name(algorithm_id)
        class_names = [input_cls, exe_cls]
        classes = []
        for cls_name in class_names:
            pre_modules, actual_name = cls_name.split(":")
            module = load_module(f"{algorithm_id}.{pre_modules}")
            cls = get_class_from_module(module, actual_name)
            classes.append(cls)
        InputClass, ExecClass = classes

        input_instance = InputClass(bam=bam, **input_data)
        output_instance = ExecClass().run(input_instance, **kwargs)
        return output_instance.model_dump()
