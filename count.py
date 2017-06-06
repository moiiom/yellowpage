city_path = "conf/cities.csv"


def read_cities():
    city_dict = dict()
    with open(city_path, 'r') as f:
        for line in f:
            info = line.replace('\n', '').split('\t')
            abbr = info[0]
            cities = info[2].split(',')
            city_dict[abbr] = cities
    return city_dict


city_dict = read_cities()

total = 0
for k, v in city_dict.items():
    total += len(v)

print 'total:{0:d}'.format(total)
