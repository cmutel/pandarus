"""Calculate intersections between two maps."""
import logging
import math
import multiprocessing
from logging.handlers import QueueHandler
from typing import Any, Dict, List, Optional, Tuple

from shapely.errors import TopologicalError
from shapely.geometry import shape

from ..errors import PoolTaskError
from ..model import Map
from .geometry import clean_geom, get_geom_kind, get_intersection
from .logger import logger_init
from .projection import project_geom


def chunker(iterable: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split an iterable into chunks of size ``chunk_size``."""
    return [iterable[i : i + chunk_size] for i in range(0, len(iterable), chunk_size)]


def worker_init(logging_queue: multiprocessing.Queue) -> None:
    """Initialize a worker."""
    # Needed to pass logging messages from child processes to a queue
    # handler which in turn passes them onto queue listener
    queue_handler = QueueHandler(logging_queue)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(queue_handler)


def get_jobs(
    map_size: int,
    max_jobs: int = 200,
    max_chunk_size: int = 20,
) -> Tuple[int, int]:
    """Get number of jobs and chunk size for multiprocessing."""
    # Want a reasonable chunk size
    # But also want a maximum of 200 jobs
    # Both numbers picked more or less at random...
    chunk_size = max(max_chunk_size, map_size // max_jobs)
    num_jobs = math.ceil(map_size / chunk_size)
    return chunk_size, num_jobs


def intersection_worker(
    from_map: str,
    from_objs: Optional[List[int]],
    to_map: str,
    worker_id: int = 1,
) -> Dict[Tuple[int, str], Any]:
    """Multiprocessing worker for map matching"""
    logging.info(
        """
        Starting intersection_worker:
        from map: %s
        from objs: %s %d to %d)
        to map: %s
        worker id: %d
        """,
        from_map,
        len(from_objs or []) or "all",
        min(from_objs or [0]),
        max(from_objs or [0]),
        to_map,
        worker_id,
    )

    results: Dict[Tuple[int, str], Any] = {}

    to_map = Map(to_map)
    if to_map.geom_type not in ("Polygon", "MultiPolygon"):
        raise ValueError("`to_map` geometry must be polygons")
    rtree_index = to_map.create_rtree_index()

    logging.info("Worker %d: Loaded `to` map.", worker_id)

    from_map = Map(from_map)
    try:
        kind = get_geom_kind(from_map)
    except KeyError as exc:
        raise ValueError(f"No valid geometry type in map {from_map}") from exc

    logging.info("Worker %d: Loaded `from` map.", worker_id)

    if from_objs:
        from_gen = ((index, from_map[index]) for index in from_objs)
    else:
        from_gen = enumerate(from_map)

    for from_index, from_obj in from_gen:
        try:
            to_shape = project_geom(shape(from_obj["geometry"]), from_map.crs, "")
            geom = clean_geom(to_shape)

            for k, v in get_intersection(
                geom, kind, to_map, rtree_index.intersection(geom.bounds), project_geom
            ).items():
                results[(from_index, k)] = v

        except TopologicalError:
            logging.exception("Skipping topological error.")
            continue
        except Exception:
            logging.exception("Intersection worker failed.")
            raise

    return results


def intersection_dispatcher(
    from_map: str,
    to_map: str,
    from_objs: Optional[List[int]] = None,
    cpus: Optional[int] = None,
    log_dir: Optional[str] = None,
) -> Dict[Tuple[int, str], Any]:
    """Dispatch intersection workers."""
    if not cpus:
        return intersection_worker(from_map, None, to_map)

    if from_objs:
        map_size = len(from_objs)
        ids = from_objs
    else:
        map_size = len(Map(from_map))
        ids = list(range(map_size))

    chunk_size, num_jobs = get_jobs(map_size)

    queue_listener, logging_queue = logger_init(log_dir)
    logging.info(
        """
        Starting `intersect` calculation.
        From map: %s
        To map: %s
        Map size: %d
        Chunk size: %d
        Number of jobs: %d
        """,
        from_map,
        to_map,
        map_size,
        chunk_size,
        num_jobs,
    )

    results: Dict[Tuple[int, str], Any] = {}

    def callback_func(data: Dict[Tuple[int, str], Any]) -> None:
        results.update(data)

    with multiprocessing.Pool(
        cpus or multiprocessing.cpu_count(), worker_init, [logging_queue]
    ) as pool:
        function_results = [
            pool.apply_async(intersection_worker, argument, callback=callback_func)
            for argument in [
                (from_map, chunk, to_map, index)
                for index, chunk in enumerate(chunker(ids, chunk_size))
            ]
        ]
        list(map(lambda fr: fr.wait(), function_results))

        if any(not fr.successful() for fr in function_results):
            raise PoolTaskError

    queue_listener.stop()

    logging.info(
        """
        Finished `intersect` calculation.
        From map: %s
        To map: %s
        Map size: %d
        Chunk size: %d
        Number of jobs: %d
        """,
        from_map,
        to_map,
        map_size,
        chunk_size,
        num_jobs,
    )

    return results
