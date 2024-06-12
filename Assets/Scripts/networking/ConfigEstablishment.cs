using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Linq;
using Debug = UnityEngine.Debug;
using System.Text.RegularExpressions;

public class AmbiguousServiceException : Exception {
    public AmbiguousServiceException(string message) : base(message) {} 
}
public class UnknownServiceException : Exception {
    public UnknownServiceException(string message) : base(message) {} 
}
public static class ConfigEstablishment {
    public static void ShareServicesWithPeers(Self self, List<Peer> peers) {
        self.SetServices(self.packages.SelectMany(p => p.GetAllThatImplement(typeof(IService)).Concat(p.GetAllThatImplement(typeof(IWrapper)))).ToList());
        DataList dl = new(content: self.services.Select(t => (IEntry)new Entry<string>("service", t.FullName)).ToList());
        peers.ForEach(p => p.SendDataList(dl));
        peers.ForEach(p => p.SetServices(p.ReceiveDataList().GetContent<string>().Select(e => e.data).ToList()));
    }

    public static void DetermineUsedServices(Self self, List<Peer> peers, VirtualNetwork virtualNetwork) {
        var required = virtualNetwork.nodes.Select(n => n.name).ToList();
        bool possible = true;
        List<(string fullName, Type type)> matches = null;
        try {
            var peerServices = peers.SelectMany(p => p.services).ToList();
            matches = MatchServices(self.services, peerServices, required);
        } catch (Exception ex) when (ex is AmbiguousServiceException || ex is UnknownServiceException) {
            Debug.Log(ex);
            possible = false;
        }
        peers.ForEach(p => p.SendEntry(new Entry<long>("possible", possible ? 1 : 0)));
        var othersPossible = peers.Select(p => (Entry<long>)p.ReceiveEntry()).All(e => e!=null && e.data == 1);
        if(possible && othersPossible) {
            matches.Zip(virtualNetwork.nodes, (p, node) => (p.fullName, node)).ToList()
                    .ForEach(p => { p.node.name = p.fullName; });
            self.SetUsedServices(matches.Where(p => p.type != null).Select(p => p.type).ToList());
        } else {
            Debug.Log("Application virtual network is not possible... Terminating");
            Debug.Break();
        }
    }

    public static List<(string fullName, Type type)> MatchServices(List<Type> local, List<string> remote, List<string> required) {
        var localMatches = required.Select(req => 
            local.Select(loc => (loc, Regex.Match(loc.FullName, @$"^(\w+\.)*{Regex.Escape(req)}$"))).Where(p => p.Item2.Success));
        var remoteMatches = required.Select(req => 
            remote.Select(rem => Regex.Match(rem, @$"^(\w+\.)*{Regex.Escape(req)}$")).Where(m => m.Success));
        return required.Zip(localMatches, (req, loc) => (req, loc)).Zip(remoteMatches, (z, rem) => (z.req, z.loc, rem)).Select(z => {
            if (z.loc.Count() + z.rem.Count() == 0) {
                throw new UnknownServiceException($"Couldn't find service '{z.req}' in either local or remote packages");
            } else if (z.loc.Count() == 1) {
                return (z.loc.First().Item2.Groups[0].Value, z.loc.First().loc);
            } else if (z.rem.Count() == 1) {
                return (z.rem.First().Groups[0].Value, null);
            } else {
                throw new AmbiguousServiceException($"Couldn't disambiguate service '{z.req}' in either local or remote packages, please use a more specific identifier");
            } 
        }).ToList();
    }

    // def match_services(local: list[str], external: list[str], required: list[str]):
    //     local_matches = [[m for m in map(lambda p: re.match(rf"^(\w+\.)*{re.escape(s)}$", p), local) if m] for s in required]
    //     external_matches = [[m for m in map(lambda p: re.match(rf"^(\w+\.)*{re.escape(s)}$", p), external) if m] for s in required]
    //     match_list: list[tuple[str, bool]] = []
    //     for req,loc,ext in zip(required, local_matches, external_matches):
    //         if len(loc) + len(ext) == 0:
    //             raise UnknownServiceException(f"Couldn't find service '{req}' in either local or remote packages")
    //         elif len(loc) == 1:
    //             match_list.append((loc[0].group(0), True))
    //         elif len(ext) == 1:
    //             match_list.append((ext[0].group(0), False))
    //         else:
    //             raise AmbiguousServiceException(f"Couldn't disambiguate service '{req}' in either local or remote packages, please use a more specific identifier") 
    //     return match_list
}