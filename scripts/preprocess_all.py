import os.path
from argparse import ArgumentParser
import subprocess


from process import regions


PBS = b"""
#PBS -l nodes=1:ppn=1
#PBS -l walltime=01:00:00

# PARAMS: REGION, TIME_PERIOD, OUTDIR

module load python
module load gdal
export PYTHONPATH=
export CPLUS_INCLUDE_PATH=/modules/gdal/2.2.3/include
export C_INCLUDE_PATH=/modules/gdal/2.2.3/include

pushd ${TMPDIR}

python3 -m venv env
source env/bin/activate

git clone https://github.com/pacificclimate/p2a-rule-engine
pushd p2a-rule-engine
git checkout feature/preprocess
pip install -U pip && pip install -i https://pypi.pacificclimate.org/simple .
pip install -U "netcdf4<1.4"

OUTFILE=${REGION}_${TIME_PERIOD}.json

python scripts/process.py -c ./data/rules.csv -d ${TIME_PERIOD} -r ${REGION} -l DEBUG > ${OUTFILE}
if [ $? -eq 0 ]; then
    rsync -v ${OUTFILE} ${OUTDIR}
else
    exit 1
fi
"""

def create_dispatch(region, time_period, outdir, email):
    params = {
        "REGION": region,
        "TIME_PERIOD": time_period,
        "OUTDIR": outdir,
    }
    vars = ",".join(f'{key}="{val}"' for key, val in params.items())
    return f"qsub -j oe -v {vars} -M {email} -N p2a_{region}_{time_period}"


def main(args):
    outdir = args.output_dir
    for region in regions.keys():
        for time_period in ['2020', '2050', '2080']:

            # Avoid rerunning duplicates
            outfile = f"{region}_{time_period}.json"
            gluster_outfile = os.path.join(outdir, outfile)

            if not os.path.exists(gluster_outfile):
                dispatch = create_dispatch(region, time_period, outdir, args.output_email)
                subprocess.run(dispatch, shell=True, input=PBS)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-o', '--output_dir', required=True)
    parser.add_argument('-e', '--output_email', default="nobody@example.com")
    args = parser.parse_args()
    main(args)
    
