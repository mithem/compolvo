create database if not exists compolvo;

use compolvo;

create or replace table customer
(
    stripe_id     int      not null,
    id            int auto_increment
        primary key,
    name          text     null,
    email         text     not null,
    password_hash longtext null,
    constraint email
        unique (email) using hash
);

create or replace table agent
(
    id                    int auto_increment
        primary key,
    customer              int      not null,
    last_connection_start datetime null,
    constraint agent_customer
        foreign key (customer) references customer (id)
);

create or replace table service
(
    name             text                                        not null,
    id               int auto_increment
        primary key,
    retrieval_data   text                                        not null,
    retrieval_method enum ('command', 'apt', 'compolvo_package') not null
);

create or replace table agent_software
(
    id                int auto_increment
        primary key,
    agent             int        not null,
    service           int        not null,
    installed_version tinytext   null,
    corrupt           tinyint(1) null,
    constraint agent_software_agent
        foreign key (agent) references agent (id),
    constraint agent_software_service
        foreign key (service) references service (id)
);

create or replace table service_offering
(
    id            int auto_increment
        primary key,
    name          text     not null,
    description   longtext null,
    price         float    not null,
    duration_days int      not null,
    service       int      not null,
    constraint service_offering_service
        foreign key (service) references service (id)
);

create or replace table service_plans
(
    id       int auto_increment
        primary key,
    service  int  not null,
    customer int  not null,
    started  date not null,
    constraint service_plan_customer
        foreign key (customer) references customer (id),
    constraint service_plan_service
        foreign key (service) references service (id)
);

create or replace table payment
(
    id           int auto_increment
        primary key,
    service_plan int      not null,
    amount       float    not null,
    date         datetime null,
    constraint payment_service_plan
        foreign key (service_plan) references service_plans (id)
);


