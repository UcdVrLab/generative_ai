using System;
using System.Collections.Generic;
using System.Linq;

public class Package {
    public string name;

    public Package(string _name) {
        name = _name;
    }

    public List<Type> GetAllThatImplement(Type type) {
        return Util.GetTypesInNamespace(name).Where(t => type.IsAssignableFrom(t)).ToList();
    }
        
    public bool IsWrapper() {
        return name.StartsWith("Wrappers");
    }
}
public class Self {
    public string name;
    public List<Package> packages;
    public List<Type> services;
    public List<Type> usedServices;

    public Self(string _name, List<Package> _packages) {
        (name, packages) = (_name, _packages);
    }

    public void SetServices(List<Type> services) {
        this.services = services;
    }
    public void SetUsedServices(List<Type> services) {
        usedServices = services;
    }
}