import rich_click as click
from rich.console import Console
from rich import inspect
import os
import subprocess
import shutil
import yaml
from AOS.preflight import Preflight


@click.command(
        context_settings=dict(
            help_option_names=["-h", "--help"]
            )
    )
@click.option(
    '-i',
    '--bamdir',
    required=True,
    type=click.Path(exists=True),
    help='Specify directory that contains your bamfiles.'
)
@click.option(
    '-o',
    '--outputdir',
    required=True,
    help='Specify output directory.'
)
@click.option(
    '-g',
    '--gtf',
    type=click.Path(exists=True),
    required=True,
    help='Specify a gtf file containing gene annotation. Will be used to extract TSS.'
)
@click.option(
    '-r',
    '--genomefasta',
    type=click.Path(exists=True),
    required=True,
    help='Specify a fasta file that contains the reference genome.'
)
@click.option(
    '-p',
    '--snakemakeprofile',
    required=True,
    help='specify the name of your snakemake profile.'
)
@click.option(
    '-b',
    '--readattractingregions',
    type=click.Path(exists=True),
    required=True,
    help='Specify a bed file containing read attracting regions. Should contain the mitochondrial genome at least.'
)
@click.option(
    '-m',
    '--motifs',
    type=click.Path(exists=True),
    help='Specify a file containing motifs. Needs to be in meme format.'
)
@click.option(
    '-f',
    '--fragsize',
    default=150,
    type=int,
    show_default=True,
    help='Specify the maximum fragment size (bps). Sits at 150 bps by default to capture only NFR (nucleosome-free region).'
)
@click.option(
    '--samplesheet',
    default='',
    help='specify a samplesheet (as a tsv file). See Readme for formatting.'
)
@click.option(
    '--comparison',
    default='',
    help='specify yaml file with comparisons. Required if a samplesheet is given.'
)
@click.option(
    '--interaction',
    default=False,
    is_flag=True,
    help='Wether or not to add interactions in the differential calculations. (e.g. ~factor1*factor2 is set, ~factor1+factor2 if not set).'
)
@click.option(
    '--mitostring',
    required=False,
    default='MT',
    show_default=True,
    help='Name of the mitochondrial contig. Defaults to MT.'
)
@click.option(
    '--upstreamuro',
    required=False,
    default=20000,
    show_default=True,
    help='Maximum permitted distance upstream of a feature (peak annotation).'
)
@click.option(
    '--downstreamuro',
    required=False,
    default=15000,
    show_default=True,
    help='Maximum permitted distance downstream of a feature (peak annotation).'
)
@click.option(
    '--featureuro',
    required=False,
    default='gene',
    show_default=True,
    help='the feature in the GTF file (column 3) to use for peak annotation.'
)
@click.option(
    '--pseudocount',
    required=False,
    default=8,
    show_default=True,
    help='Pseudocount to add to the count matrix prior to differential calling.'
)
@click.option(
    '--peakset',
    required=False,
    default=None,
    show_default=True,
    help='Include an external peak file (bed format).'
)
def main(bamdir,
        outputdir,
        gtf,
        genomefasta,
        readattractingregions,
        motifs,
        fragsize,
        snakemakeprofile,
        samplesheet,
        comparison,
        interaction,
        mitostring,
        upstreamuro,
        downstreamuro,
        featureuro,
        pseudocount,
        peakset
        ):
    # Init
    pf = Preflight(**locals())
    # GTF
    print("Sorting GTF & creating TSS.bed..")
    pf.genTSS()
    # comparisons.
    print("Double checking comparisons (if present)..")
    pf.checkcomps()
    # Check fasta file.
    print("Checking fasta formatting and inferring ESS..")
    pf.checkFna()
    print("ESS set at: {}".format(pf.vars['genomesize']))
    # Write conf
    print("Writing config file in {}..".format(
        os.path.basename(pf.dirs['outputdir'])
    ))
    #
    pf.dumpconf()
    #inspect(pf)
    console = Console()
    with console.status("[bold green] Running snakemake..."): 
        subprocess.run(
            [
                'snakemake',
                '-s', pf.rules['wf'],
                '--profile', pf.vars['snakemakeprofile'],
                '--max-jobs-per-second', '1',
                '-p',
                '--configfile', pf.files['configfile'],
                '-d', pf.dirs['outputdir']
            ]
        )
            