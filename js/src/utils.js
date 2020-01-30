import PSemaphore from 'promise-semaphore';

const delay = (sec) => new Promise((resolve) => setTimeout(resolve, sec*1000));

/**
 * Map a function onto a list where fn is being called at a limit of 'rate' number of calls per second.
 * and 'room' number of parallel calls.
 * Note that the minimum window at which rate is respected is room/rate seconds.
 */
export
const batchRateMap = (list, fn, {room, rate}) => {
    var queue = new PSemaphore({rooms: room})
    return list.map(async (value) => {
        return new Promise((valueResolve, reject) => {
            queue.add(() => {
                // We may not want to start the next job directly, we want to respect the
                // throttling/rate, e.g.:
                // If we have room for 10 parallel jobs, at a max rate of 100/second, each job
                // should take at least 10/100=0.1 seconds.
                // If we have room for 100 parallel jobs, and a max rate of 10/second, each
                // job should take 100/10=10 seconds. But it will have a burst of 100 calls.
                const throttlePromise = delay(room/rate);
                // If the job is done, resolve the promise immediately, don't want for the throttle Promise
                // This means that if we have room for 10 parallel jobs
                // and just 9 jobs, we will never have to wait for the throttlePromise
                const resultPromise = fn(value).then(valueResolve);
                return Promise.all([resultPromise, throttlePromise]);
            });
        });
    });
}
