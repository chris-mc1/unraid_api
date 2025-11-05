# Plan d'implémentation : Gestion des VMs et Docker

Ce document décrit le plan détaillé pour ajouter la gestion des machines virtuelles (VMs) et des conteneurs Docker à l'intégration Home Assistant pour Unraid.

## 📋 Phase 1: Exploration de l'API GraphQL Unraid

**Objectif**: Identifier les queries et mutations disponibles pour VMs et Docker

### 1.1 Rechercher la documentation de l'API GraphQL d'Unraid

- Identifier les queries pour lister les VMs et conteneurs
- Identifier les mutations pour contrôler les VMs (start, stop, pause, restart, force stop)
- Identifier les mutations pour contrôler les conteneurs Docker (start, stop, restart, pause, unpause)

### 1.2 Tester les queries GraphQL

- Vérifier les champs disponibles pour chaque type d'entité
- Comprendre les états possibles (running, stopped, paused, etc.)
- Identifier les métriques disponibles (CPU, mémoire, réseau, etc.)

---

## 🏗️ Phase 2: Modèles de données

**Fichier**: `custom_components/unraid_api/models.py`

### 2.1 Créer des enums pour les états

```python
class VmState(StrEnum):
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting-down"
    # autres états selon l'API...

class DockerState(StrEnum):
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    RESTARTING = "restarting"
    # autres états selon l'API...
```

### 2.2 Créer des dataclasses pour VMs et Docker

```python
@dataclass
class VirtualMachine:
    id: str
    name: str
    state: VmState
    cpu_count: int
    memory: int  # en MB
    autostart: bool
    # métriques si disponibles dans l'API
    cpu_usage: float | None
    memory_usage: int | None

@dataclass
class DockerContainer:
    id: str
    name: str
    state: DockerState
    image: str
    autostart: bool
    # métriques si disponibles dans l'API
    cpu_usage: float | None
    memory_usage: int | None
    network_rx: int | None
    network_tx: int | None
```

---

## 🔌 Phase 3: Extension de l'API Client

**Fichier**: `custom_components/unraid_api/api/v4_20.py`

### 3.1 Ajouter les queries GraphQL

```python
VMS_QUERY = """
query VMs {
  vms {
    id
    name
    state
    cpuCount
    memory
    autostart
    # autres champs selon l'API...
  }
}
"""

DOCKER_QUERY = """
query Docker {
  docker {
    containers {
      id
      name
      state
      image
      autostart
      # autres champs selon l'API...
    }
  }
}
"""
```

### 3.2 Ajouter les mutations pour le contrôle

```python
VM_START_MUTATION = """
mutation StartVM($id: String!) {
  vmStart(id: $id) { success }
}
"""

VM_STOP_MUTATION = """
mutation StopVM($id: String!) {
  vmStop(id: $id) { success }
}
"""

# Similaire pour:
# - VM_RESTART_MUTATION
# - VM_PAUSE_MUTATION
# - VM_FORCE_STOP_MUTATION

DOCKER_START_MUTATION = """
mutation StartContainer($id: String!) {
  dockerStart(id: $id) { success }
}
"""

DOCKER_STOP_MUTATION = """
mutation StopContainer($id: String!) {
  dockerStop(id: $id) { success }
}
"""

# Similaire pour:
# - DOCKER_RESTART_MUTATION
# - DOCKER_PAUSE_MUTATION
# - DOCKER_UNPAUSE_MUTATION
```

### 3.3 Implémenter les méthodes dans UnraidApiV420

#### Méthodes de query

```python
async def query_vms(self) -> list[VirtualMachine]:
    """Récupérer la liste des VMs."""
    response = await self.call_api(VMS_QUERY, VmsQuery)
    return [
        VirtualMachine(
            id=vm.id,
            name=vm.name,
            state=vm.state,
            cpu_count=vm.cpu_count,
            memory=vm.memory,
            autostart=vm.autostart,
            cpu_usage=vm.cpu_usage,
            memory_usage=vm.memory_usage,
        )
        for vm in response.vms
    ]

async def query_docker_containers(self) -> list[DockerContainer]:
    """Récupérer la liste des conteneurs Docker."""
    response = await self.call_api(DOCKER_QUERY, DockerQuery)
    return [
        DockerContainer(
            id=container.id,
            name=container.name,
            state=container.state,
            image=container.image,
            autostart=container.autostart,
            cpu_usage=container.cpu_usage,
            memory_usage=container.memory_usage,
            network_rx=container.network_rx,
            network_tx=container.network_tx,
        )
        for container in response.docker.containers
    ]
```

#### Méthodes de contrôle VMs

```python
async def vm_start(self, vm_id: str) -> bool:
    """Démarrer une VM."""

async def vm_stop(self, vm_id: str) -> bool:
    """Arrêter une VM."""

async def vm_restart(self, vm_id: str) -> bool:
    """Redémarrer une VM."""

async def vm_pause(self, vm_id: str) -> bool:
    """Mettre en pause une VM."""

async def vm_force_stop(self, vm_id: str) -> bool:
    """Forcer l'arrêt d'une VM."""
```

#### Méthodes de contrôle Docker

```python
async def docker_start(self, container_id: str) -> bool:
    """Démarrer un conteneur Docker."""

async def docker_stop(self, container_id: str) -> bool:
    """Arrêter un conteneur Docker."""

async def docker_restart(self, container_id: str) -> bool:
    """Redémarrer un conteneur Docker."""

async def docker_pause(self, container_id: str) -> bool:
    """Mettre en pause un conteneur Docker."""

async def docker_unpause(self, container_id: str) -> bool:
    """Reprendre un conteneur Docker."""
```

### 3.4 Créer les classes Pydantic pour la validation

```python
# VMs
class VmsQuery(BaseModel):
    vms: list[_VM]

class _VM(BaseModel):
    id: str
    name: str
    state: VmState
    cpu_count: int = Field(alias="cpuCount")
    memory: int
    autostart: bool
    cpu_usage: float | None = Field(alias="cpuUsage", default=None)
    memory_usage: int | None = Field(alias="memoryUsage", default=None)

# Docker
class DockerQuery(BaseModel):
    docker: _Docker

class _Docker(BaseModel):
    containers: list[_Container]

class _Container(BaseModel):
    id: str
    name: str
    state: DockerState
    image: str
    autostart: bool
    cpu_usage: float | None = Field(alias="cpuUsage", default=None)
    memory_usage: int | None = Field(alias="memoryUsage", default=None)
    network_rx: int | None = Field(alias="networkRx", default=None)
    network_tx: int | None = Field(alias="networkTx", default=None)
```

---

## 🔄 Phase 4: Mise à jour du Coordinator

**Fichier**: `custom_components/unraid_api/coordinator.py`

### 4.1 Ajouter les constantes de configuration

```python
CONF_VMS = "vms"
CONF_DOCKER = "docker"
```

### 4.2 Étendre le dictionnaire de données

```python
UnraidDataUpdateCoordinatorData = TypedDict(
    "UnraidDataUpdateCoordinatorData",
    {
        "metrics": Metrics | None,
        "array": Array | None,
        "disks": dict[str, Disk],
        "shares": dict[str, Share],
        "vms": dict[str, VirtualMachine],           # nouveau
        "docker": dict[str, DockerContainer],       # nouveau
    },
)
```

### 4.3 Ajouter les queries dans _async_update_data()

```python
async def _async_update_data(self) -> UnraidDataUpdateCoordinatorData:
    """Fetch data from API endpoint."""
    try:
        async with asyncio.TaskGroup() as group:
            metrics_task = group.create_task(self.client.query_metrics())
            array_task = group.create_task(self.client.query_array())

            disks_task = None
            if self.config_entry.options.get(CONF_DRIVES, True):
                disks_task = group.create_task(self.client.query_disks())

            shares_task = None
            if self.config_entry.options.get(CONF_SHARES, True):
                shares_task = group.create_task(self.client.query_shares())

            # Nouveau: VMs
            vms_task = None
            if self.config_entry.options.get(CONF_VMS, True):
                vms_task = group.create_task(self.client.query_vms())

            # Nouveau: Docker
            docker_task = None
            if self.config_entry.options.get(CONF_DOCKER, True):
                docker_task = group.create_task(self.client.query_docker_containers())

        # Traiter les VMs
        vms: dict[str, VirtualMachine] = {}
        if vms_task:
            vm_list = vms_task.result()
            for vm in vm_list:
                vms[vm.id] = vm
                if vm.id not in self._known_vm_ids:
                    self._known_vm_ids.add(vm.id)
                    self._call_vm_listeners(vm.id)

        # Traiter les conteneurs Docker
        docker: dict[str, DockerContainer] = {}
        if docker_task:
            container_list = docker_task.result()
            for container in container_list:
                docker[container.id] = container
                if container.id not in self._known_docker_ids:
                    self._known_docker_ids.add(container.id)
                    self._call_docker_listeners(container.id)

        return {
            "metrics": metrics_task.result(),
            "array": array_task.result(),
            "disks": disks,
            "shares": shares,
            "vms": vms,
            "docker": docker,
        }
```

### 4.4 Ajouter les listeners pour les nouvelles entités

```python
def __init__(self, ...):
    # Existant
    self._disk_listener_removers: dict[str, Callable[[], None]] = {}
    self._share_listener_removers: dict[str, Callable[[], None]] = {}
    self._known_disk_ids: set[str] = set()
    self._known_share_names: set[str] = set()

    # Nouveau
    self._vm_listener_removers: dict[str, Callable[[], None]] = {}
    self._docker_listener_removers: dict[str, Callable[[], None]] = {}
    self._known_vm_ids: set[str] = set()
    self._known_docker_ids: set[str] = set()

def _call_vm_listeners(self, vm_id: str) -> None:
    """Call listeners for a new VM."""
    for update_callback in list(self._vm_listener_removers.get(vm_id, {}).keys()):
        update_callback()

def _call_docker_listeners(self, container_id: str) -> None:
    """Call listeners for a new Docker container."""
    for update_callback in list(self._docker_listener_removers.get(container_id, {}).keys()):
        update_callback()

def async_add_vm_listener(
    self, vm_id: str, update_callback: Callable[[], None]
) -> Callable[[], None]:
    """Listen for data updates for a specific VM."""

def async_add_docker_listener(
    self, container_id: str, update_callback: Callable[[], None]
) -> Callable[[], None]:
    """Listen for data updates for a specific Docker container."""
```

### 4.5 Ajouter des méthodes de contrôle

```python
async def async_vm_action(self, vm_id: str, action: str) -> bool:
    """Execute an action on a VM."""
    actions = {
        "start": self.client.vm_start,
        "stop": self.client.vm_stop,
        "restart": self.client.vm_restart,
        "pause": self.client.vm_pause,
        "force_stop": self.client.vm_force_stop,
    }
    if action not in actions:
        raise ValueError(f"Unknown VM action: {action}")

    result = await actions[action](vm_id)
    await self.async_request_refresh()
    return result

async def async_docker_action(self, container_id: str, action: str) -> bool:
    """Execute an action on a Docker container."""
    actions = {
        "start": self.client.docker_start,
        "stop": self.client.docker_stop,
        "restart": self.client.docker_restart,
        "pause": self.client.docker_pause,
        "unpause": self.client.docker_unpause,
    }
    if action not in actions:
        raise ValueError(f"Unknown Docker action: {action}")

    result = await actions[action](container_id)
    await self.async_request_refresh()
    return result
```

---

## 🎛️ Phase 5: Nouvelles entités Home Assistant

### Phase 5A: Sensors pour VMs

**Fichier**: `custom_components/unraid_api/sensor.py`

#### 5A.1 Créer des descriptions d'entités pour VMs

```python
@dataclass(frozen=True, kw_only=True)
class UnraidVmSensorEntityDescription(SensorEntityDescription):
    """Describes Unraid VM sensor entity."""
    value_fn: Callable[[VirtualMachine], StateType]
    extra_values_fn: Callable[[VirtualMachine], dict[str, Any]] | None = None

VM_SENSORS: tuple[UnraidVmSensorEntityDescription, ...] = (
    UnraidVmSensorEntityDescription(
        key="vm_state",
        translation_key="vm_state",
        device_class=SensorDeviceClass.ENUM,
        options=[state.value for state in VmState],
        value_fn=lambda vm: vm.state.value,
    ),
    UnraidVmSensorEntityDescription(
        key="vm_cpu_usage",
        translation_key="vm_cpu_usage",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value_fn=lambda vm: vm.cpu_usage,
    ),
    UnraidVmSensorEntityDescription(
        key="vm_memory_usage",
        translation_key="vm_memory_usage",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        value_fn=lambda vm: vm.memory_usage,
        extra_values_fn=lambda vm: {
            "total_memory": vm.memory,
            "cpu_count": vm.cpu_count,
            "autostart": vm.autostart,
        },
    ),
)
```

#### 5A.2 Créer la classe UnraidVmSensor

```python
class UnraidVmSensor(UnraidEntity, SensorEntity):
    """Representation of an Unraid VM sensor."""

    entity_description: UnraidVmSensorEntityDescription

    def __init__(
        self,
        coordinator: UnraidDataUpdateCoordinator,
        description: UnraidVmSensorEntityDescription,
        vm_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._vm_id = vm_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}-{description.key}-{vm_id}"

    @property
    def vm(self) -> VirtualMachine | None:
        """Return the VM."""
        return self.coordinator.data["vms"].get(self._vm_id)

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if (vm := self.vm) is None:
            return None
        return self.entity_description.value_fn(vm)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if (vm := self.vm) is None:
            return None
        if self.entity_description.extra_values_fn:
            return self.entity_description.extra_values_fn(vm)
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        if (vm := self.vm) is None:
            return {}
        return DeviceInfo(
            identifiers={(DOMAIN, f"vm_{self._vm_id}")},
            name=f"VM {vm.name}",
            manufacturer="Unraid",
            model="Virtual Machine",
            via_device=(DOMAIN, self.coordinator.config_entry.entry_id),
        )
```

#### 5A.3 Mettre à jour async_setup_entry

```python
async def async_setup_entry(
    hass: HomeAssistant,
    entry: UnraidConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Unraid sensors."""
    coordinator = entry.runtime_data

    # Sensors existants...

    # VM Sensors
    if entry.options.get(CONF_VMS, True):
        @callback
        def async_add_vm_sensor(vm_id: str) -> None:
            """Add VM sensor."""
            async_add_entities(
                UnraidVmSensor(coordinator, description, vm_id)
                for description in VM_SENSORS
            )

        for vm_id in coordinator.data["vms"]:
            async_add_vm_sensor(vm_id)

        coordinator.async_add_vm_listener(None, async_add_vm_sensor)
```

### Phase 5B: Sensors pour Docker

**Fichier**: `custom_components/unraid_api/sensor.py`

#### 5B.1 Créer des descriptions similaires

```python
@dataclass(frozen=True, kw_only=True)
class UnraidDockerSensorEntityDescription(SensorEntityDescription):
    """Describes Unraid Docker sensor entity."""
    value_fn: Callable[[DockerContainer], StateType]
    extra_values_fn: Callable[[DockerContainer], dict[str, Any]] | None = None

DOCKER_SENSORS: tuple[UnraidDockerSensorEntityDescription, ...] = (
    UnraidDockerSensorEntityDescription(
        key="docker_state",
        translation_key="docker_state",
        device_class=SensorDeviceClass.ENUM,
        options=[state.value for state in DockerState],
        value_fn=lambda container: container.state.value,
    ),
    UnraidDockerSensorEntityDescription(
        key="docker_cpu_usage",
        translation_key="docker_cpu_usage",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value_fn=lambda container: container.cpu_usage,
    ),
    UnraidDockerSensorEntityDescription(
        key="docker_memory_usage",
        translation_key="docker_memory_usage",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIGABYTES,
        value_fn=lambda container: container.memory_usage,
    ),
    UnraidDockerSensorEntityDescription(
        key="docker_network_rx",
        translation_key="docker_network_rx",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        value_fn=lambda container: container.network_rx,
    ),
    UnraidDockerSensorEntityDescription(
        key="docker_network_tx",
        translation_key="docker_network_tx",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        value_fn=lambda container: container.network_tx,
        extra_values_fn=lambda container: {
            "image": container.image,
            "autostart": container.autostart,
        },
    ),
)
```

#### 5B.2 Créer la classe UnraidDockerSensor

Similaire à `UnraidVmSensor` mais pour les conteneurs Docker.

### Phase 5C: Switches pour contrôle

**Nouveau fichier**: `custom_components/unraid_api/switch.py`

#### 5C.1 Créer UnraidVmSwitch

```python
class UnraidVmSwitch(UnraidEntity, SwitchEntity):
    """Representation of an Unraid VM switch."""

    def __init__(
        self,
        coordinator: UnraidDataUpdateCoordinator,
        vm_id: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._vm_id = vm_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}-vm_switch-{vm_id}"
        self._attr_translation_key = "vm_power"

    @property
    def vm(self) -> VirtualMachine | None:
        """Return the VM."""
        return self.coordinator.data["vms"].get(self._vm_id)

    @property
    def is_on(self) -> bool | None:
        """Return true if VM is running."""
        if (vm := self.vm) is None:
            return None
        return vm.state == VmState.RUNNING

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the VM."""
        await self.coordinator.async_vm_action(self._vm_id, "start")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the VM."""
        await self.coordinator.async_vm_action(self._vm_id, "stop")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        if (vm := self.vm) is None:
            return {}
        return DeviceInfo(
            identifiers={(DOMAIN, f"vm_{self._vm_id}")},
            name=f"VM {vm.name}",
            manufacturer="Unraid",
            model="Virtual Machine",
            via_device=(DOMAIN, self.coordinator.config_entry.entry_id),
        )
```

#### 5C.2 Créer UnraidDockerSwitch

Similaire à `UnraidVmSwitch` mais pour les conteneurs Docker.

### Phase 5D: Buttons pour actions

**Nouveau fichier**: `custom_components/unraid_api/button.py`

#### 5D.1 Créer les boutons pour VMs

```python
@dataclass(frozen=True, kw_only=True)
class UnraidVmButtonEntityDescription(ButtonEntityDescription):
    """Describes Unraid VM button entity."""
    action: str

VM_BUTTONS: tuple[UnraidVmButtonEntityDescription, ...] = (
    UnraidVmButtonEntityDescription(
        key="vm_restart",
        translation_key="vm_restart",
        device_class=ButtonDeviceClass.RESTART,
        action="restart",
    ),
    UnraidVmButtonEntityDescription(
        key="vm_force_stop",
        translation_key="vm_force_stop",
        action="force_stop",
    ),
    UnraidVmButtonEntityDescription(
        key="vm_pause",
        translation_key="vm_pause",
        action="pause",
    ),
)

class UnraidVmButton(UnraidEntity, ButtonEntity):
    """Representation of an Unraid VM button."""

    entity_description: UnraidVmButtonEntityDescription

    def __init__(
        self,
        coordinator: UnraidDataUpdateCoordinator,
        description: UnraidVmButtonEntityDescription,
        vm_id: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.entity_description = description
        self._vm_id = vm_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}-{description.key}-{vm_id}"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_vm_action(self._vm_id, self.entity_description.action)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        vm = self.coordinator.data["vms"].get(self._vm_id)
        if vm is None:
            return {}
        return DeviceInfo(
            identifiers={(DOMAIN, f"vm_{self._vm_id}")},
            name=f"VM {vm.name}",
            manufacturer="Unraid",
            model="Virtual Machine",
            via_device=(DOMAIN, self.coordinator.config_entry.entry_id),
        )
```

#### 5D.2 Créer les boutons pour Docker

Similaire aux boutons VM mais pour Docker (restart, pause, unpause).

---

## ⚙️ Phase 6: Configuration

**Fichier**: `custom_components/unraid_api/config_flow.py`

### 6.1 Ajouter les constantes

```python
# Dans const.py
CONF_VMS = "vms"
CONF_DOCKER = "docker"
```

### 6.2 Mettre à jour le schéma d'options

```python
class UnraidOptionsFlow(OptionsFlow):
    """Handle Unraid options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the Unraid options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DRIVES,
                        default=self.config_entry.options.get(CONF_DRIVES, True),
                    ): bool,
                    vol.Optional(
                        CONF_SHARES,
                        default=self.config_entry.options.get(CONF_SHARES, True),
                    ): bool,
                    vol.Optional(
                        CONF_VMS,
                        default=self.config_entry.options.get(CONF_VMS, True),
                    ): bool,
                    vol.Optional(
                        CONF_DOCKER,
                        default=self.config_entry.options.get(CONF_DOCKER, True),
                    ): bool,
                }
            ),
        )
```

### 6.3 Mettre à jour __init__.py

```python
# Dans __init__.py
async def async_setup_entry(hass: HomeAssistant, entry: UnraidConfigEntry) -> bool:
    """Set up Unraid from a config entry."""
    # ... code existant ...

    await hass.config_entries.async_forward_entry_setups(
        entry,
        [
            Platform.SENSOR,
            Platform.BINARY_SENSOR,
            Platform.SWITCH,      # nouveau
            Platform.BUTTON,      # nouveau
        ],
    )
```

---

## 📝 Phase 7: Traductions

**Fichier**: `custom_components/unraid_api/translations/en.json`

### 7.1 Ajouter les traductions pour VMs

```json
{
  "entity": {
    "sensor": {
      "vm_state": {
        "name": "State",
        "state": {
          "running": "Running",
          "stopped": "Stopped",
          "paused": "Paused",
          "shutting-down": "Shutting down"
        }
      },
      "vm_cpu_usage": {
        "name": "CPU usage"
      },
      "vm_memory_usage": {
        "name": "Memory usage"
      },
      "docker_state": {
        "name": "State",
        "state": {
          "running": "Running",
          "stopped": "Stopped",
          "paused": "Paused",
          "restarting": "Restarting"
        }
      },
      "docker_cpu_usage": {
        "name": "CPU usage"
      },
      "docker_memory_usage": {
        "name": "Memory usage"
      },
      "docker_network_rx": {
        "name": "Network received"
      },
      "docker_network_tx": {
        "name": "Network transmitted"
      }
    },
    "switch": {
      "vm_power": {
        "name": "Power"
      },
      "docker_power": {
        "name": "Power"
      }
    },
    "button": {
      "vm_restart": {
        "name": "Restart"
      },
      "vm_force_stop": {
        "name": "Force stop"
      },
      "vm_pause": {
        "name": "Pause"
      },
      "docker_restart": {
        "name": "Restart"
      },
      "docker_pause": {
        "name": "Pause"
      },
      "docker_unpause": {
        "name": "Unpause"
      }
    }
  },
  "config": {
    "step": {
      "user": {
        "description": "Enter your Unraid server details",
        "data": {
          "host": "Host URL",
          "api_key": "API Key",
          "verify_ssl": "Verify SSL certificate"
        }
      }
    }
  },
  "options": {
    "step": {
      "init": {
        "description": "Configure what to monitor",
        "data": {
          "drives": "Monitor drives",
          "shares": "Monitor shares",
          "vms": "Monitor VMs",
          "docker": "Monitor Docker containers"
        }
      }
    }
  }
}
```

---

## 🧪 Phase 8: Tests

### 8.1 Créer des réponses GraphQL mockées

**Fichier**: `tests/graphql_responses.py`

```python
MOCK_VMS_RESPONSE = {
    "data": {
        "vms": [
            {
                "id": "vm1",
                "name": "Ubuntu VM",
                "state": "running",
                "cpuCount": 4,
                "memory": 8192,
                "autostart": True,
                "cpuUsage": 25.5,
                "memoryUsage": 4096,
            },
            {
                "id": "vm2",
                "name": "Windows VM",
                "state": "stopped",
                "cpuCount": 2,
                "memory": 4096,
                "autostart": False,
                "cpuUsage": None,
                "memoryUsage": None,
            },
        ]
    }
}

MOCK_DOCKER_RESPONSE = {
    "data": {
        "docker": {
            "containers": [
                {
                    "id": "container1",
                    "name": "plex",
                    "state": "running",
                    "image": "plexinc/pms-docker",
                    "autostart": True,
                    "cpuUsage": 10.2,
                    "memoryUsage": 2048,
                    "networkRx": 1024000,
                    "networkTx": 512000,
                },
                {
                    "id": "container2",
                    "name": "nginx",
                    "state": "stopped",
                    "image": "nginx:latest",
                    "autostart": False,
                    "cpuUsage": None,
                    "memoryUsage": None,
                    "networkRx": None,
                    "networkTx": None,
                },
            ]
        }
    }
}

MOCK_VM_START_RESPONSE = {
    "data": {
        "vmStart": {
            "success": True
        }
    }
}

MOCK_DOCKER_START_RESPONSE = {
    "data": {
        "dockerStart": {
            "success": True
        }
    }
}
```

### 8.2 Ajouter des tests pour l'API

**Fichier**: `tests/test_api.py`

```python
async def test_query_vms(
    unraid_api_v420: UnraidApiV420,
    mock_aioresponse: aioresponses,
) -> None:
    """Test querying VMs."""
    mock_aioresponse.post(
        "https://unraid.local/graphql",
        payload=MOCK_VMS_RESPONSE,
    )

    vms = await unraid_api_v420.query_vms()
    assert len(vms) == 2
    assert vms[0].id == "vm1"
    assert vms[0].name == "Ubuntu VM"
    assert vms[0].state == VmState.RUNNING
    assert vms[0].cpu_count == 4

async def test_query_docker_containers(
    unraid_api_v420: UnraidApiV420,
    mock_aioresponse: aioresponses,
) -> None:
    """Test querying Docker containers."""
    mock_aioresponse.post(
        "https://unraid.local/graphql",
        payload=MOCK_DOCKER_RESPONSE,
    )

    containers = await unraid_api_v420.query_docker_containers()
    assert len(containers) == 2
    assert containers[0].id == "container1"
    assert containers[0].name == "plex"
    assert containers[0].state == DockerState.RUNNING

async def test_vm_start(
    unraid_api_v420: UnraidApiV420,
    mock_aioresponse: aioresponses,
) -> None:
    """Test starting a VM."""
    mock_aioresponse.post(
        "https://unraid.local/graphql",
        payload=MOCK_VM_START_RESPONSE,
    )

    result = await unraid_api_v420.vm_start("vm1")
    assert result is True
```

### 8.3 Ajouter des tests pour les entités

**Nouveau fichier**: `tests/test_switch.py`

```python
async def test_vm_switch_turn_on(
    hass: HomeAssistant,
    mock_unraid_entry: UnraidConfigEntry,
) -> None:
    """Test turning on a VM via switch."""
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.unraid_vm_ubuntu_vm"},
        blocking=True,
    )
    # Assertions...

async def test_docker_switch_turn_off(
    hass: HomeAssistant,
    mock_unraid_entry: UnraidConfigEntry,
) -> None:
    """Test turning off a Docker container via switch."""
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.unraid_docker_plex"},
        blocking=True,
    )
    # Assertions...
```

**Nouveau fichier**: `tests/test_button.py`

```python
async def test_vm_restart_button(
    hass: HomeAssistant,
    mock_unraid_entry: UnraidConfigEntry,
) -> None:
    """Test restarting a VM via button."""
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.unraid_vm_ubuntu_vm_restart"},
        blocking=True,
    )
    # Assertions...
```

---

## 📦 Phase 9: Mise à jour de la documentation

### 9.1 Mettre à jour README.md

Ajouter une section décrivant:
- Les nouvelles entités pour VMs
- Les nouvelles entités pour Docker
- Exemples d'automatisations
- Services disponibles

### 9.2 Mettre à jour manifest.json

```json
{
  "domain": "unraid_api",
  "name": "Unraid API",
  "version": "1.4.0",
  "documentation": "https://github.com/domalab/ha-unraid",
  "requirements": [],
  "codeowners": ["@domalab"],
  "config_flow": true,
  "iot_class": "local_polling",
  "dependencies": [],
  "homeassistant": "2024.10.0"
}
```

---

## 🚀 Phase 10: Commits et PR

### 10.1 Plan de commits

1. **Commit 1**: Add VM and Docker data models
2. **Commit 2**: Add GraphQL queries and mutations for VMs and Docker
3. **Commit 3**: Update coordinator with VM and Docker support
4. **Commit 4**: Add VM and Docker sensors
5. **Commit 5**: Add VM and Docker switches
6. **Commit 6**: Add VM and Docker buttons
7. **Commit 7**: Add configuration options for VMs and Docker
8. **Commit 8**: Add translations for new entities
9. **Commit 9**: Add tests for new functionality
10. **Commit 10**: Update documentation

### 10.2 Push et PR

```bash
git push -u origin claude/add-vm-management-011CUqPQHmPkqftpYbrc4G13
gh pr create --title "Add VM and Docker management support" --body "..."
```

---

## 📊 Résumé des nouvelles entités créées

### Entités par VM

| Type | Entité | Description |
|------|--------|-------------|
| **Sensor** | State | État de la VM (running, stopped, paused, shutting-down) |
| **Sensor** | CPU Usage | Utilisation CPU de la VM (%) |
| **Sensor** | Memory Usage | Utilisation mémoire de la VM (MB → GB) |
| **Switch** | Power | Allumer/éteindre la VM |
| **Button** | Restart | Redémarrer la VM |
| **Button** | Force Stop | Forcer l'arrêt de la VM |
| **Button** | Pause | Mettre en pause/reprendre la VM |

### Entités par conteneur Docker

| Type | Entité | Description |
|------|--------|-------------|
| **Sensor** | State | État du conteneur (running, stopped, paused, restarting) |
| **Sensor** | CPU Usage | Utilisation CPU du conteneur (%) |
| **Sensor** | Memory Usage | Utilisation mémoire du conteneur (MB → GB) |
| **Sensor** | Network RX | Données reçues (bytes) |
| **Sensor** | Network TX | Données transmises (bytes) |
| **Switch** | Power | Démarrer/arrêter le conteneur |
| **Button** | Restart | Redémarrer le conteneur |
| **Button** | Pause | Mettre en pause le conteneur |
| **Button** | Unpause | Reprendre le conteneur |

---

## 🔧 Configuration requise

### Options de configuration

Après cette implémentation, les utilisateurs pourront configurer:
- **Monitor drives**: Surveiller les disques (existant)
- **Monitor shares**: Surveiller les partages (existant)
- **Monitor VMs**: Surveiller les machines virtuelles (nouveau)
- **Monitor Docker containers**: Surveiller les conteneurs Docker (nouveau)

### Exemple d'utilisation dans Home Assistant

```yaml
# Automation example: Start VM when home
automation:
  - alias: "Start work VM when I arrive"
    trigger:
      - platform: state
        entity_id: person.john
        to: "home"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.unraid_vm_work_vm

# Automation example: Stop all Docker containers at night
automation:
  - alias: "Stop media containers at night"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: switch.turn_off
        target:
          entity_id:
            - switch.unraid_docker_plex
            - switch.unraid_docker_sonarr
            - switch.unraid_docker_radarr
```

---

## 📚 Références et ressources

### Documentation à consulter

1. **Unraid GraphQL API Documentation**
   - Explorer l'API GraphQL via l'interface Web d'Unraid
   - URL: `https://your-unraid-server/graphql`
   - Utiliser GraphiQL pour explorer le schéma

2. **Home Assistant Developer Documentation**
   - [Entity Platform](https://developers.home-assistant.io/docs/core/entity/)
   - [Switch Platform](https://developers.home-assistant.io/docs/core/entity/switch/)
   - [Button Platform](https://developers.home-assistant.io/docs/core/entity/button/)
   - [Data Update Coordinator](https://developers.home-assistant.io/docs/integration_fetching_data/)

3. **Pydantic Documentation**
   - [Field Aliases](https://docs.pydantic.dev/latest/concepts/fields/#field-aliases)
   - [Model Validation](https://docs.pydantic.dev/latest/concepts/models/)

---

## ⚠️ Points d'attention

### Sécurité

- S'assurer que les mutations nécessitent une API key avec les permissions appropriées
- Gérer les erreurs d'autorisation correctement
- Ne pas exposer de données sensibles dans les logs

### Performance

- Les queries VMs et Docker doivent être exécutées en parallèle avec les autres queries
- Éviter les requêtes trop fréquentes (respecter l'intervalle de 1 minute)
- Gérer correctement le cas où il y a beaucoup de VMs/conteneurs

### Compatibilité

- Vérifier la version minimale de l'API Unraid requise pour les nouvelles fonctionnalités
- Gérer les cas où certaines métriques ne sont pas disponibles (retourner None)
- Assurer la rétrocompatibilité avec les installations existantes

### Expérience utilisateur

- Fournir des noms d'entités clairs et cohérents
- Ajouter des attributs supplémentaires pertinents (autostart, image, etc.)
- Documenter clairement les actions disponibles et leurs effets

---

## ✅ Checklist finale

Avant de considérer l'implémentation comme terminée:

- [ ] Toutes les queries GraphQL fonctionnent correctement
- [ ] Toutes les mutations GraphQL fonctionnent correctement
- [ ] Les entités sont créées dynamiquement pour les nouvelles VMs/conteneurs
- [ ] Les switches peuvent démarrer/arrêter les VMs et conteneurs
- [ ] Les boutons exécutent correctement les actions (restart, pause, etc.)
- [ ] Les tests passent à 100%
- [ ] La documentation est à jour
- [ ] Les traductions sont complètes
- [ ] Le code respecte les conventions Home Assistant
- [ ] Les erreurs sont gérées correctement
- [ ] Les performances sont acceptables
- [ ] L'intégration fonctionne avec plusieurs serveurs Unraid
- [ ] La configuration peut être modifiée sans redémarrage complet
