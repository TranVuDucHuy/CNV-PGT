from algorithm import AlgorithmPlugin, BaseInput, BaseOutput, SampleSegment, SampleBin


class InputClass(BaseInput):
    input_1: str
    input_2: int


class OutputClass(BaseOutput):
    output_1: str
    output_2: str


class ExeClass(AlgorithmPlugin):
    def run(self, input_data: InputClass, **kwargs) -> OutputClass:
        output = OutputClass(
            reference_genome="GRCh37/hg19",
            segments=[
                SampleSegment(
                    chromosome="X",
                    start=100,
                    end=200,
                    copy_number=2.0,
                    confidence=0.95,
                )
            ],
            bins=[
                SampleBin(
                    chromosome="Y",
                    start=100,
                    end=200,
                    copy_number=2.0,
                    read_count=150,
                    gc_content=0.4,
                )
            ],
            output_1=f"Processed {input_data.input_1} with kwargs {kwargs}",
            output_2=f"Input bam has the length of {len(input_data.bam)} bytes",
        )
        return output
